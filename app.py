# app.py  –  CV Rating Analyzer  (parallel LLM calls + Start/Stop + persistence)
# ---------------------------------------------------------------------------

import os, uuid, tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
import traceback

import streamlit as st

# Your own modules
from parser import CVParser
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

st.set_page_config(page_title="Analisador de CV", layout="wide")
st.title("Analisador de CV")

# ───────────────────────── Session state ───────────────────────────────────
ss = st.session_state
ss.setdefault("processing", False)      # are we currently running?
ss.setdefault("start_pipeline", False)  # run heavy code on this rerun?
ss.setdefault("stop_requested", False)  # user clicked stop?
ss.setdefault("last_run", None)         # cached df & excel path

# ───────────────────────── Inputs ──────────────────────────────────────────
job_description = st.text_area("Cole a Descrição da Vaga aqui", height=200)

uploaded_files = st.file_uploader(
    "Faça upload dos CVs dos candidatos em PDF", type=["pdf"], accept_multiple_files=True
)

# ───────────────────────── Start / Stop buttons ───────────────────────────
if ss.processing:
    if st.button("🛑  Parar", key="stop_btn"):
        ss.stop_requested = True
        st.warning("Parada solicitada — finalizando etapa atual…")
else:
    if st.button("🟢  Processar", key="process_btn"):
        ss.processing = True
        ss.start_pipeline = True
        st.rerun()         # rerun immediately so Stop appears

# ───────────────────────── Heavy pipeline ─────────────────────────────────
if ss.start_pipeline:
    if not (job_description and uploaded_files):
        st.error("Por favor, forneça a descrição da vaga e pelo menos um PDF.")
        ss.processing = ss.start_pipeline = False

    else:
        try:
            progress_container = st.container()
            status_placeholder = st.empty()
            with progress_container:
                overall_progress = st.progress(0)

            # 1️⃣  Save uploaded PDFs ---------------------------------------------------
            status_placeholder.write("Preparando arquivos…")
            with st.spinner("Preparando arquivos…"):
                tmpdir = tempfile.mkdtemp()
                for i, f in enumerate(uploaded_files):
                    if ss.stop_requested:
                        raise RuntimeError("Stopped by user")
                    with open(os.path.join(tmpdir, f.name), "wb") as out:
                        out.write(f.read())
                    overall_progress.progress((i + 1) / len(uploaded_files) * 0.15)

            # 2️⃣  Parse CVs (parallel) ----------------------------------------------------
            status_placeholder.write(f"Analisando CVs…")
            with st.spinner("Analisando CVs…"):
                if ss.stop_requested:
                    raise RuntimeError("Stopped by user")
                
                parser = CVParser(tmpdir)
                parsed_cvs = parser.parse(max_workers=8)
                overall_progress.progress(0.15)

            # 3️⃣  Extract info (parallel LLM calls) -----------------------------------
            status_placeholder.write(f"Extraindo informações… (0/{len(parsed_cvs)})")
            with st.spinner("Extraindo informações…"):
                extractor = ExtractionAgent()

                def _extract(cv):
                    return extractor.extract(cv)

                infos, completed = [], 0
                with ThreadPoolExecutor(max_workers=min(12, len(parsed_cvs))) as ex:
                    futures = {ex.submit(_extract, cv): cv for cv in parsed_cvs}
                    for fut in as_completed(futures):
                        if ss.stop_requested:
                            raise RuntimeError("Stopped by user")
                        infos.append(fut.result())
                        completed += 1
                        p = 0.15 + (completed / len(parsed_cvs)) * 0.35
                        overall_progress.progress(p)
                        status_placeholder.write(
                            f"Extraindo informações… ({completed}/{len(parsed_cvs)})"
                        )

            # 4️⃣  Rate candidates (parallel LLM calls) ---------------------------------
            status_placeholder.write(f"Avaliando candidatos… (0/{len(infos)})")
            with st.spinner("Avaliando candidatos…"):
                rater = RatingAgent(job_description)

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
                        p = 0.50 + (completed / len(infos)) * 0.20
                        overall_progress.progress(p)
                        status_placeholder.write(
                            f"Avaliando candidatos… ({completed}/{len(infos)})"
                        )

            # 5️⃣  Judge all candidates (parallel LLM calls) --------------------------------
            status_placeholder.write("Julgando avaliações para justiça e consistência…")
            with st.spinner("Julgando avaliações…"):
                if ss.stop_requested:
                    raise RuntimeError("Stopped by user")
                
                # Create progress bar for judge step
                judge_progress = st.progress(0)
                judge_status = st.empty()
                
                def update_judge_progress(progress, status_text):
                    judge_progress.progress(progress)
                    judge_status.write(status_text)
                
                judge = JudgeAgent(job_description, batch_size=5)  # Process in batches of 5
                # Use parallel processing with max_workers=4 for judge batches
                judge_ratings = judge.judge_all(infos, ratings, progress_callback=update_judge_progress, max_workers=4)
                
                # Verify all candidates were processed
                if len(judge_ratings) != len(infos):
                    st.warning(f"Aviso: Apenas {len(judge_ratings)} de {len(infos)} candidatos foram julgados. Alguns podem ter sido pulados devido a erros de processamento.")
                
                judge_progress.progress(1.0)
                judge_status.write("✅ Etapa de julgamento concluída!")
                overall_progress.progress(0.90)

            # 6️⃣  Combine + Excel -------------------------------------------------------
            print("Number of infos:", len(infos))
            print("Number of judge_ratings:", len(judge_ratings))
            print("INFO files:", [info.file for info in infos])
            print("JUDGE files:", [rating.file for rating in judge_ratings])
            status_placeholder.write("Gerando relatório final…")
            with st.spinner("Gerando relatório…"):
                df = combine(infos, ratings, judge_ratings).reset_index(drop=True)
                print("Number of rows in final DataFrame:", len(df))
                print("DataFrame columns:", df.columns.tolist())
                if 'file' in df.columns:
                    print("Files in final DataFrame:", df['file'].tolist())
                if 'candidate_id' in df.columns:
                    print("Candidate IDs in final DataFrame:", df['candidate_id'].tolist())
                if len(df) != len(infos):
                    st.warning(f"Aviso: {len(infos) - len(df)} candidatos estão faltando na tabela final. Verifique se há erros de análise ou avaliação.")
                excel_path = os.path.join(tmpdir, f"cv_ratings_{uuid.uuid4().hex}.xlsx")
                to_excel(df, excel_path)
                overall_progress.progress(1.0)

            status_placeholder.write("✅ Processamento concluído!")
            st.success("Concluído!")

            # Cache for future reruns
            ss.last_run = {"df": df, "excel_path": excel_path}
            ss.setdefault("tmpdirs", []).append(tmpdir)

        except RuntimeError as stop_err:
            st.warning(str(stop_err))

        except Exception as e:
            st.error(f"Ocorreu um erro: {e}")
            st.error(traceback.format_exc())

        finally:
            ss.processing = ss.start_pipeline = ss.stop_requested = False

# ───────────────────────── Show cached results ────────────────────────────
if ss.last_run:
    cached = ss.last_run
    st.subheader("Últimos resultados")
    st.dataframe(cached["df"])

    with open(cached["excel_path"], "rb") as f:
        st.download_button(
            "📥 Baixar Excel",
            f,
            file_name="cv_ratings.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            key="download_cached"
        )
