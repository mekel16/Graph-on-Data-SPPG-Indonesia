from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.answer_generator import generate_province_summary
from app.db import close_connection, verify_connection
from app.llm_router import IntentResult, classify_question
from app.observability import Timer, init_logging, log_query
from app.queries import (
    count_by_kabupaten,
    count_by_kecamatan,
    list_by_kecamatan,
    ranking_kabupaten,
    run_query,
    search_by_alamat,
    search_by_desa,
    summary_by_province,
    top_kabupaten_by_province,
)
from app.resolver import resolve_city, resolve_districts
from app.text_to_cypher import generate_cypher


@asynccontextmanager
async def lifespan(app: FastAPI):
    verify_connection()
    init_logging()

    yield

    close_connection()


app = FastAPI(
    title="SPPG Graph Question Answering API",
    version="1.0.0",
    lifespan=lifespan,
)


class QuestionRequest(BaseModel):
    question: str


def format_count_answer(result: dict) -> str:
    jumlah = result.get("jumlah", 0)
    wilayah = result.get("wilayah", [])

    if not wilayah:
        return "Wilayah tersebut tidak ditemukan di database."

    item = wilayah[0]

    kecamatan = item.get("kecamatan", "")
    kabupaten = item.get("kabupaten_kota", "")
    provinsi = item.get("provinsi", "")

    return (
        f"Terdapat {jumlah} SPPG di Kecamatan "
        f"{kecamatan}, {kabupaten}, {provinsi}."
    )


def format_list_answer(rows: list[dict]) -> str:
    if not rows:
        return "Tidak ditemukan data SPPG."

    lines = [
        f"Ditemukan {len(rows)} data SPPG:"
    ]

    for index, row in enumerate(rows, start=1):
        nama = row.get("nama") or "-"
        desa = row.get("desa") or "-"
        alamat = row.get("alamat") or "-"

        lines.append(
            f"{index}. {nama} "
            f"(Desa/Kelurahan: {desa}) - {alamat}"
        )

    return "\n".join(lines)


def format_ambiguous_district_answer(
    candidates: list[dict],
) -> str:
    options = [
        (
            f"{item['kecamatan']}, "
            f"{item['kabupaten_kota']}, "
            f"{item['provinsi']}"
        )
        for item in candidates
    ]

    return (
        "Nama kecamatan tersebut ditemukan di beberapa wilayah. "
        "Silakan sebutkan kabupaten/kotanya: "
        + "; ".join(options)
    )


def resolve_district(
    intent: IntentResult,
) -> dict[str, Any]:
    if not intent.kecamatan:
        return {
            "status": "need_context",
            "candidates": [],
        }

    candidates = resolve_districts(
        kecamatan=intent.kecamatan,
        kabupaten_kota=intent.kabupaten_kota,
        provinsi=intent.provinsi,
    )

    if not candidates:
        return {
            "status": "not_found",
            "candidates": [],
        }

    if len(candidates) > 1:
        return {
            "status": "ambiguous",
            "candidates": candidates,
        }

    return {
        "status": "resolved",
        "candidates": candidates,
    }


def execute_intent(
    question: str,
    intent: IntentResult,
) -> dict:
    # =================================================
    # 1. Hitung SPPG berdasarkan kecamatan
    # =================================================
    if intent.intent == "count_sppg_by_kecamatan":
        resolution = resolve_district(intent)

        if resolution["status"] == "need_context":
            return {
                "status": "need_context",
                "answer": (
                    "Sebutkan nama kecamatan yang ingin dihitung."
                ),
            }

        if resolution["status"] == "not_found":
            return {
                "status": "not_found",
                "answer": (
                    f"Kecamatan '{intent.kecamatan}' "
                    "tidak ditemukan di database."
                ),
            }

        if resolution["status"] == "ambiguous":
            return {
                "status": "ambiguous",
                "answer": format_ambiguous_district_answer(
                    resolution["candidates"]
                ),
                "candidates": resolution["candidates"],
            }

        resolved = resolution["candidates"][0]

        result = count_by_kecamatan(
            kecamatan=resolved["kecamatan_normalized"],
            kabupaten_kota=resolved[
                "kabupaten_kota_normalized"
            ],
            provinsi=resolved["provinsi_normalized"],
        )

        return {
            "status": "success",
            "result": result,
            "answer": format_count_answer(result),
            "cypher_type": "COUNT_BY_KECAMATAN",
        }

    # =================================================
    # 2. Daftar SPPG berdasarkan kecamatan
    # =================================================
    if intent.intent == "list_sppg_by_kecamatan":
        resolution = resolve_district(intent)

        if resolution["status"] == "need_context":
            return {
                "status": "need_context",
                "answer": (
                    "Sebutkan nama kecamatan yang ingin ditampilkan."
                ),
            }

        if resolution["status"] == "not_found":
            return {
                "status": "not_found",
                "answer": (
                    f"Kecamatan '{intent.kecamatan}' "
                    "tidak ditemukan di database."
                ),
            }

        if resolution["status"] == "ambiguous":
            return {
                "status": "ambiguous",
                "answer": format_ambiguous_district_answer(
                    resolution["candidates"]
                ),
                "candidates": resolution["candidates"],
            }

        resolved = resolution["candidates"][0]

        rows = list_by_kecamatan(
            kecamatan=resolved["kecamatan_normalized"],
            kabupaten_kota=resolved[
                "kabupaten_kota_normalized"
            ],
            provinsi=resolved["provinsi_normalized"],
            limit=intent.limit,
        )

        return {
            "status": "success",
            "result": rows,
            "answer": format_list_answer(rows),
            "cypher_type": "LIST_BY_KECAMATAN",
        }

    # =================================================
    # 3. Hitung SPPG berdasarkan kabupaten/kota
    # =================================================
    if intent.intent == "count_sppg_by_kabupaten":
        if not intent.kabupaten_kota:
            return {
                "status": "need_context",
                "answer": (
                    "Sebutkan nama kabupaten atau kota "
                    "yang ingin dihitung."
                ),
            }

        candidates = resolve_city(
            kabupaten_kota=intent.kabupaten_kota,
            provinsi=intent.provinsi,
        )

        if not candidates:
            return {
                "status": "not_found",
                "answer": (
                    f"Kabupaten/kota "
                    f"'{intent.kabupaten_kota}' "
                    "tidak ditemukan di database."
                ),
            }

        if len(candidates) > 1:
            options = [
                f"{item['kabupaten_kota']}, "
                f"{item['provinsi']}"
                for item in candidates
            ]

            return {
                "status": "ambiguous",
                "answer": (
                    "Nama kabupaten/kota tersebut ditemukan "
                    "di beberapa provinsi: "
                    + "; ".join(options)
                ),
                "candidates": candidates,
            }

        resolved = candidates[0]

        result = count_by_kabupaten(
            kabupaten_kota=resolved[
                "kabupaten_kota_normalized"
            ],
            provinsi=resolved["provinsi_normalized"],
        )

        jumlah = result.get("jumlah", 0)

        return {
            "status": "success",
            "result": result,
            "answer": (
                f"Terdapat {jumlah} SPPG di "
                f"{resolved['kabupaten_kota']}, "
                f"{resolved['provinsi']}."
            ),
            "cypher_type": "COUNT_BY_KABUPATEN",
        }

    # =================================================
    # 4. Ranking kabupaten berdasarkan jumlah SPPG
    # =================================================
    if intent.intent == "ranking_sppg_by_kabupaten":
        rows = ranking_kabupaten(
            provinsi=intent.provinsi,
            limit=intent.limit,
        )

        if not rows:
            return {
                "status": "success",
                "result": [],
                "answer": "Tidak ditemukan data ranking.",
                "cypher_type": "RANKING_KABUPATEN",
            }

        lines = [
            (
                f"{index}. "
                f"{row['kabupaten_kota']} "
                f"({row['provinsi']}): "
                f"{row['jumlah_sppg']} SPPG"
            )
            for index, row in enumerate(rows, start=1)
        ]

        return {
            "status": "success",
            "result": rows,
            "answer": "\n".join(lines),
            "cypher_type": "RANKING_KABUPATEN",
        }

    # =================================================
    # 5. Cari SPPG berdasarkan desa
    # =================================================
    if intent.intent == "search_sppg_by_desa":
        if not intent.desa:
            return {
                "status": "need_context",
                "answer": (
                    "Sebutkan nama desa atau kelurahan."
                ),
            }

        rows = search_by_desa(
            desa=intent.desa,
            kecamatan=intent.kecamatan,
            kabupaten_kota=intent.kabupaten_kota,
            limit=intent.limit,
        )

        return {
            "status": "success",
            "result": rows,
            "answer": format_list_answer(rows),
            "cypher_type": "SEARCH_BY_DESA",
        }

    # =================================================
    # 6. Cari SPPG berdasarkan alamat
    # =================================================
    if intent.intent == "search_sppg_by_alamat":
        if not intent.keyword:
            return {
                "status": "need_context",
                "answer": (
                    "Sebutkan kata kunci alamat "
                    "yang ingin dicari."
                ),
            }

        rows = search_by_alamat(
            keyword=intent.keyword,
            limit=intent.limit,
        )

        return {
            "status": "success",
            "result": rows,
            "answer": format_list_answer(rows),
            "cypher_type": "SEARCH_BY_ALAMAT",
        }

    # =================================================
    # 7. Analisis kondisi SPPG berdasarkan provinsi
    # =================================================
    if intent.intent == "summary_by_province":
        if not intent.provinsi:
            return {
                "status": "need_context",
                "answer": (
                    "Sebutkan nama provinsi "
                    "yang ingin dianalisis."
                ),
            }

        summary_result = summary_by_province(
            provinsi=intent.provinsi,
        )

        if not summary_result.get("found"):
            return {
                "status": "not_found",
                "answer": (
                    f"Provinsi '{intent.provinsi}' "
                    "tidak ditemukan di database."
                ),
            }

        top_kabupaten = top_kabupaten_by_province(
            provinsi=intent.provinsi,
            limit=10,
        )

        province_data = {
            "summary": summary_result["summary"],
            "top_kabupaten": top_kabupaten,
        }

        answer = generate_province_summary(
            province_data
        )

        return {
            "status": "success",
            "result": province_data,
            "answer": answer,
            "cypher_type": "SUMMARY_BY_PROVINCE",
        }

    # =================================================
    # 8. Intent tidak dikenali
    # =================================================
    return {
        "status": "unknown",
    }


@app.get("/")
def root():
    return {
        "message": "SPPG GraphRAG API aktif",
        "docs": "/docs",
        "health": "/health",
    }


@app.get("/health")
def health():
    return {
        "status": "ok",
        "service": "sppg-graph-qa",
    }


@app.post("/ask")
def ask(request: QuestionRequest):
    timer = Timer()
    question = request.question.strip()

    if not question:
        raise HTTPException(
            status_code=400,
            detail="Pertanyaan tidak boleh kosong.",
        )

    intent = None
    parameters = {}
    cypher = None
    result = None

    try:
        # ---------------------------------------------
        # Tahap 1: LLM memahami pertanyaan
        # ---------------------------------------------
        intent = classify_question(question)
        parameters = intent.model_dump()

        # ---------------------------------------------
        # Tahap 2: Jalankan intent
        # ---------------------------------------------
        routed_result = execute_intent(
            question=question,
            intent=intent,
        )

        # Jika intent dikenali
        if routed_result.get("status") != "unknown":
            result = routed_result.get("result")

            log_query(
                question=question,
                intent=intent.intent,
                parameters=parameters,
                cypher=routed_result.get("cypher_type"),
                result=result,
                duration_ms=timer.elapsed_ms(),
                success=True,
            )

            return {
                "question": question,
                "intent": intent.model_dump(),
                **routed_result,
            }

        # ---------------------------------------------
        # Tahap 3: Fallback Text-to-Cypher
        # ---------------------------------------------
        generated = generate_cypher(question)

        cypher = generated.cypher
        parameters = generated.params

        result = run_query(
            query=cypher,
            params=parameters,
        )

        log_query(
            question=question,
            intent="text_to_cypher",
            parameters=parameters,
            cypher=cypher,
            result=result,
            duration_ms=timer.elapsed_ms(),
            success=True,
        )

        return {
            "question": question,
            "intent": "text_to_cypher",
            "cypher": cypher,
            "result": result,
            "answer": (
                "Query berhasil dijalankan. "
                "Hasil data tersedia pada field result."
            ),
        }

    except Exception as error:
        log_query(
            question=question,
            intent=(
                intent.intent
                if intent
                else "classification_failed"
            ),
            parameters=parameters,
            cypher=cypher,
            result=result,
            duration_ms=timer.elapsed_ms(),
            success=False,
            error=str(error),
        )

        raise HTTPException(
            status_code=500,
            detail={
                "message": (
                    "Terjadi kesalahan saat "
                    "memproses pertanyaan."
                ),
                "error": str(error),
            },
        )