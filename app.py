# app.py  –  CV Rating Analyzer  (parallel LLM calls + Start/Stop + persistence)
# ---------------------------------------------------------------------------

import os, uuid, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

import streamlit as st

# Your own modules
from parser import CVParser
from agent_cleaning import CleaningAgent
from agent_extraction import ExtractionAgent
from agent_rating import RatingAgent
from agent_judge import JudgeAgent
from combiner import combine
from formatter import to_excel


# ───────────────────────── CSS (button colours) ────────────────────────────
st.markdown(
    """
    <style>
    button[data-baseweb="button"][id^="process_btn"] {
        background-color: #28a745 !important;   /* green */
        color: white !important;
    }
    button[data-baseweb="button"][id^="stop_btn"] {
        background-color: #dc3545 !important;   /* red   */
        color: white !important;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.set_page_config(page_title="CV Rating Analyzer", layout="wide")
st.title("CV Rating Analyzer")

# ───────────────────────── Session state ───────────────────────────────────
ss = st.session_state
ss.setdefault("processing", False)      # are we currently running?
ss.setdefault("start_pipeline", False)  # run heavy code on this rerun?
ss.setdefault("stop_requested", False)  # user clicked stop?
ss.setdefault("last_run", None)         # cached df & excel path

# ───────────────────────── Inputs ──────────────────────────────────────────
job_description = st.text_area("Paste the Job Description here", height=200)

uploaded_files = st.file_uploader(
    "Upload candidate CV PDFs", type=["pdf"], accept_multiple_files=True
)

# ───────────────────────── Start / Stop buttons ───────────────────────────
if ss.processing:
    if st.button("🛑  Stop", key="stop_btn"):
        ss.stop_requested = True
        st.warning("Stop requested — finishing current step…")
else:
    if st.button("🟢  Process", key="process_btn"):
        ss.processing = True
        ss.start_pipeline = True
        st.rerun()         # rerun immediately so Stop appears

# ───────────────────────── Helper (single-CV cleaning) ────────────────────
def clean_cv(cv_data):
    cleaned = CleaningAgent().clean(cv_data)
    # Ensure candidate_id is preserved
    if 'candidate_id' in cv_data:
        cleaned['candidate_id'] = cv_data['candidate_id']
    return cleaned

# ───────────────────────── Heavy pipeline ─────────────────────────────────
if ss.start_pipeline:
    if not (job_description and uploaded_files):
        st.error("Please provide job description and at least one PDF.")
        ss.processing = ss.start_pipeline = False

    else:
        try:
            progress_container = st.container()
            status_placeholder = st.empty()
            with progress_container:
                overall_progress = st.progress(0)

            # 1️⃣  Save uploaded PDFs ---------------------------------------------------
            status_placeholder.write("Preparing files…")
            with st.spinner("Preparing files…"):
                tmpdir = tempfile.mkdtemp()
                for i, f in enumerate(uploaded_files):
                    if ss.stop_requested:
                        raise RuntimeError("Stopped by user")
                    with open(os.path.join(tmpdir, f.name), "wb") as out:
                        out.write(f.read())
                    overall_progress.progress((i + 1) / len(uploaded_files) * 0.10)

            # 2️⃣  Clean job description ------------------------------------------------
            status_placeholder.write("Cleaning job description…")
            with st.spinner("Cleaning job description…"):
                cleaned_jd = CleaningAgent().clean(
                    {"file": "job_description", "content": job_description}
                )["content"]
                overall_progress.progress(0.15)

            # 3️⃣  Parse CVs (parallel) ----------------------------------------------------
            status_placeholder.write(f"Parsing CVs…")
            with st.spinner("Parsing CVs…"):
                pdf_files = [f for f in os.listdir(tmpdir) if f.lower().endswith('.pdf')]
                if not pdf_files:
                    raise RuntimeError("No PDF files found in uploaded files")
                
                parser = CVParser(tmpdir)
                parsed_cvs = parser.parse(max_workers=min(8, len(pdf_files)))
                
                # Check for parsing errors
                error_files = [cv for cv in parsed_cvs if cv.get('error')]
                if error_files:
                    st.warning(f"Warning: {len(error_files)} PDF files had parsing errors: {[cv['file'] for cv in error_files]}")
                
                status_placeholder.write(f"✅ Parsed {len(parsed_cvs)} CVs successfully")
                overall_progress.progress(0.25)

            # 4️⃣  Clean CVs (parallel) -------------------------------------------------
            status_placeholder.write(f"Cleaning CV content… (0/{len(parsed_cvs)})")
            with st.spinner("Cleaning CV content…"):
                cleaned_cvs, completed = [], 0
                with ThreadPoolExecutor(max_workers=min(8, len(parsed_cvs))) as ex:
                    futures = {ex.submit(clean_cv, cv): cv for cv in parsed_cvs}
                    for fut in as_completed(futures):
                        if ss.stop_requested:
                            raise RuntimeError("Stopped by user")
                        try:
                            cleaned_cvs.append(fut.result())
                        except Exception as err:
                            st.error(f"❌ Cleaning {futures[fut]['file']}: {err}")
                            cleaned_cvs.append(futures[fut])
                        completed += 1
                        p = 0.25 + (completed / len(parsed_cvs)) * 0.20
                        overall_progress.progress(p)
                        status_placeholder.write(
                            f"Cleaning CV content… ({completed}/{len(parsed_cvs)})"
                        )

            # 5️⃣  Extract info (parallel LLM calls) -----------------------------------
            status_placeholder.write(f"Extracting info… (0/{len(cleaned_cvs)})")
            with st.spinner("Extracting info…"):
                extractor = ExtractionAgent()

                def _extract(cv):
                    return extractor.extract(cv)

                infos, completed = [], 0
                with ThreadPoolExecutor(max_workers=min(12, len(cleaned_cvs))) as ex:
                    futures = {ex.submit(_extract, cv): cv for cv in cleaned_cvs}
                    for fut in as_completed(futures):
                        if ss.stop_requested:
                            raise RuntimeError("Stopped by user")
                        infos.append(fut.result())
                        completed += 1
                        p = 0.45 + (completed / len(cleaned_cvs)) * 0.25
                        overall_progress.progress(p)
                        status_placeholder.write(
                            f"Extracting info… ({completed}/{len(cleaned_cvs)})"
                        )

            # 6️⃣  Rate candidates (parallel LLM calls) ---------------------------------
            status_placeholder.write(f"Rating candidates… (0/{len(infos)})")
            with st.spinner("Rating candidates…"):
                rater = RatingAgent(cleaned_jd)

                def _rate(info_):
                    return rater.rate(info_)

                ratings, completed = [], 0
                with ThreadPoolExecutor(max_workers=min(12, len(infos))) as ex:
                    futures = {ex.submit(_rate, info): info for info in infos}
                    for fut in as_completed(futures):
                        if ss.stop_requested:
                            raise RuntimeError("Stopped by user")
                        ratings.append(fut.result())
                        completed += 1
                        p = 0.70 + (completed / len(infos)) * 0.15
                        overall_progress.progress(p)
                        status_placeholder.write(
                            f"Rating candidates… ({completed}/{len(infos)})"
                        )

            # 7️⃣  Judge all candidates (parallel LLM calls) --------------------------------
            status_placeholder.write("Judging ratings for fairness and consistency…")
            with st.spinner("Judging ratings…"):
                if ss.stop_requested:
                    raise RuntimeError("Stopped by user")
                
                # Create progress bar for judge step
                judge_progress = st.progress(0)
                judge_status = st.empty()
                
                def update_judge_progress(progress, status_text):
                    judge_progress.progress(progress)
                    judge_status.write(status_text)
                
                judge = JudgeAgent(cleaned_jd, batch_size=5)  # Process in batches of 5
                # Use parallel processing with max_workers=4 for judge batches
                judge_ratings = judge.judge_all(infos, ratings, progress_callback=update_judge_progress, max_workers=4)
                
                # Verify all candidates were processed
                if len(judge_ratings) != len(infos):
                    st.warning(f"Warning: Only {len(judge_ratings)} out of {len(infos)} candidates were judged. Some may have been skipped due to processing errors.")
                
                judge_progress.progress(1.0)
                judge_status.write("✅ Judge step complete!")
                overall_progress.progress(0.90)

            # 8️⃣  Combine + Excel -------------------------------------------------------
            print("Number of infos:", len(infos))
            print("Number of judge_ratings:", len(judge_ratings))
            print("INFO files:", [info.file for info in infos])
            print("JUDGE files:", [rating.file for rating in judge_ratings])
            status_placeholder.write("Generating final report…")
            with st.spinner("Generating report…"):
                df = combine(infos, ratings, judge_ratings).reset_index(drop=True)
                print("Number of rows in final DataFrame:", len(df))
                print("DataFrame columns:", df.columns.tolist())
                if 'file' in df.columns:
                    print("Files in final DataFrame:", df['file'].tolist())
                if 'candidate_id' in df.columns:
                    print("Candidate IDs in final DataFrame:", df['candidate_id'].tolist())
                if len(df) != len(infos):
                    st.warning(f"Warning: {len(infos) - len(df)} candidates are missing from the final table. Check for parsing or rating errors.")
                excel_path = os.path.join(tmpdir, f"cv_ratings_{uuid.uuid4().hex}.xlsx")
                to_excel(df, excel_path)
                overall_progress.progress(1.0)

            status_placeholder.write("✅ Processing complete!")
            st.success("Done!")

            # Cache for future reruns
            ss.last_run = {"df": df, "excel_path": excel_path}
            ss.setdefault("tmpdirs", []).append(tmpdir)

        except RuntimeError as stop_err:
            st.warning(str(stop_err))

        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.error(traceback.format_exc())

        finally:
            ss.processing = ss.start_pipeline = ss.stop_requested = False

# ───────────────────────── Show cached results ────────────────────────────
if ss.last_run:
    cached = ss.last_run
    st.subheader("Latest results")
    st.dataframe(cached["df"])

    with open(cached["excel_path"], "rb") as f:
        st.download_button(
            "📥 Download Excel",
            f,
            file_name="cv_ratings.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_cached"
        )
