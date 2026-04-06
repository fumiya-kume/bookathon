#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import time
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from google import genai  # type: ignore
from google.genai import types  # type: ignore


MODEL = "gemini-3.1-flash-image-preview"
IMAGE_SIZE = "2K"
RETRY_COUNT = 3
OUTPUT_DIR = Path("images/generated-gemini")

LOGGER = logging.getLogger("generate_gemini_diagrams")

COMMON_STYLE_PROMPT = """
白背景、書籍向けの洗練されたモノクロ図解。A5判で印刷しても文字が潰れないこと。
線は太め、装飾は最小限、情報量は1図1メッセージに限定。日本語ラベル中心。
プレゼン資料風ではなく、技術書の挿図として落ち着いたデザイン。
アイコンは補助的に使い、文章を読まなくても主旨が伝わる構図にする。
""".strip()


@dataclass(frozen=True)
class ImageSpec:
    image_id: str
    aspect_ratio: str
    prompt: str


SPECS: list[ImageSpec] = [
    ImageSpec(
        image_id="ch01-guardrail",
        aspect_ratio="16:9",
        prompt="""
「ガードレール思考」を説明する技術書向けモノクロ図解。構図は、中央に高速で前進するAIエージェント、その左右に“事前に用意された枠組み”としてのガードレールを配置する。ガードレールの左側には「公式ドキュメント」「バージョン指定」「Agent Skills / ルール」、右側には「CI」「Lint」「テスト」「レビュー基準」を配置し、AIがその枠の中を安全に高速で進む様子を描く。対比として、枠の外に逸れて失敗する細い破線ルートを1本だけ添え、「前提が曖昧だと高速で間違う」ことが伝わるようにする。ゴール地点には「正しい実装」「安定した出力」といった意味の到達点を置く。道路の比喩は使ってよいが、単なる道路標識図ではなく、実務上のガードレール要素が視覚的に読めることを重視する。
""".strip(),
    ),
    ImageSpec(
        image_id="ch02-ipo-model",
        aspect_ratio="16:9",
        prompt="""
第2章「アイデアを形にする技術」向けの図解として、「INPUT→PROCESS→OUTPUTモデル」を“仕様化のフレーム”として描く。左から右への3箱構成だが、単なる入出力図ではなく、上段に「ユーザー体験を1文で定義」、中段に「INPUT / PROCESS / OUTPUTに分解」、下段に「処理を技術要素へ分解」「画面遷移を可視化」という流れを入れる。中心メッセージは「アイデアを実装可能な仕様へ落とす」であり、「AIが埋める」は補助的な小ラベルにとどめる。例として蝶ネクタイ型変声機を小さく添え、INPUT=マイク音声、PROCESS=ピッチ変換、OUTPUT=変換音声 の対応が一目で分かるようにする。第4章の実務図と差別化するため、こちらは“思考整理・仕様分解”のニュアンスを強くする。
""".strip(),
    ),
    ImageSpec(
        image_id="input-process-output",
        aspect_ratio="16:9",
        prompt="""
第4章向けの「INPUT→PROCESS→OUTPUTモデル」図解。第2章の仕様化図とは差別化し、“AIに渡す指示フォーマット”として描く。構図は左右ではなく、上から下へ「人間の指示」「AIの処理」「生成される成果物」の3層構造にする。最上段に『入力：何を受け取るか』『出力：何を返すか』『形式：どんな形にするか』の3行テンプレートを置き、中段にAIがその指示をもとに API呼び出し・変換・推論・整形 を行う黒箱、下段に成果物として UI、音声、画像、データ一覧など複数の出力例を並べる。図の主メッセージは「人間はI/Oを定義し、AIが実装の間を埋める」。例として『現在地→近隣レストラン検索→距離順リスト表示』のような短いケースを入れる。白背景、モノクロ、テンプレート感があり、すぐ真似できそうに見える図。
""".strip(),
    ),
    ImageSpec(
        image_id="parallel-dev",
        aspect_ratio="16:9",
        prompt="""
「git worktreeによる並列開発」を説明する技術書向けモノクロ図解。上部に1つのリポジトリを置き、そこから複数のworktreeが枝分かれする構図。左と中央にはAIエージェントが担当する worktree A / worktree B を置き、それぞれ『フロントエンド』『バックエンド』『テスト』『資料作成』など別タスクを並列実行している様子を描く。右側には人間が立ち、役割を『設計』『優先順位付け』『確認』『統合判断』として示す。下部では複数の成果が master へ統合され、自動デプロイや即時検証につながる流れを矢印で示す。重要なのは「人間も実装者の1人」ではなく「ディレクター兼統合者」になっていること、そして「同時に複数タスクが進む」ことが一目で分かること。時間短縮のニュアンスを出すため、単線ではなく並列レーン構成にする。
""".strip(),
    ),
    ImageSpec(
        image_id="team-formation",
        aspect_ratio="16:9",
        prompt="""
「チーム編成で重視すべきこと」を説明する書籍向けモノクロ図解。左右比較の構図で、左に『方向性の一致』、右に『スキルの多様性』を置く。左側は複数の参加者が同じ旗・同じゴールを見ている構図で、『何を作りたいか』『誰の課題を解くか』が揃っている状態を示す。右側はコード、デザイン、ビジネスなど異なるスキルが並ぶが、AIによって一部は補完可能であることを薄い補助ラベルで添える。図全体の主メッセージは「スキル差より、作りたい方向の一致が推進力を生む」。さらに下段に小さく『AIで補いやすい：コーディング、デザインの一部』『AIで補いにくい：熱量、課題意識、方向性』の対比を入れる。勝ち負けの比較図ではなく、優先順位の違いとして上品に見せる。
""".strip(),
    ),
    ImageSpec(
        image_id="hackathon-timeline",
        aspect_ratio="16:9",
        prompt="""
「AI時代のハッカソン タイムライン変化」を説明する技術書向けモノクロ図解。上下2段比較で、上段に『従来の2日間ハッカソン』、下段に『AI時代の2日間ハッカソン』を配置する。上段は『短いアイデア出し → 長い開発 → 短い発表準備』、下段は『長いアイデア・設計 → 圧縮された開発 → 発表準備の確保』という差が一目で分かる棒グラフ型タイムラインにする。特に下段では Day1 をほぼ丸ごと『アイデア・設計』に充てられることを強調し、Day2 に『AI支援で実装』『ピッチ準備』『発表』が並ぶ構成にする。補助要素として『開発禁止期間』『アイデア変更禁止』のルールを細い破線や帯で示すが、凡例が主役にならないようにする。図の主メッセージは「AIで実装が短くなったぶん、設計と発表に時間を振り直せる」。
""".strip(),
    ),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Generate book diagrams with Gemini 3.1 Flash Image."
    )
    _ = parser.add_argument(
        "--only",
        nargs="*",
        default=[],
        help="Generate only the specified image IDs.",
    )
    _ = parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite files even if they already exist.",
    )
    _ = parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show info logs while generating images.",
    )
    _ = parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug logs including prompt previews and response details.",
    )
    return parser.parse_args()


def configure_logging(verbose: bool, debug: bool) -> None:
    level = logging.WARNING
    if verbose:
        level = logging.INFO
    if debug:
        level = logging.DEBUG

    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)s %(message)s",
        datefmt="%H:%M:%S",
    )


def select_specs(only: list[str]) -> list[ImageSpec]:
    if not only:
        return SPECS
    wanted = set(only)
    selected = [spec for spec in SPECS if spec.image_id in wanted]
    missing = wanted.difference(spec.image_id for spec in selected)
    if missing:
        raise SystemExit(f"Unknown image IDs: {', '.join(sorted(missing))}")
    return selected


def get_client() -> Any:
    api_key = os.environ.get("GOOGLE_GENAI_API_KEY")
    if not api_key:
        raise SystemExit("GOOGLE_GENAI_API_KEY is not set.")
    LOGGER.info("Using model: %s", MODEL)
    LOGGER.info("Output size: %s", IMAGE_SIZE)
    return genai.Client(api_key=api_key)


def build_prompt(spec: ImageSpec) -> str:
    return f"{spec.prompt}\n\n共通指定:\n{COMMON_STYLE_PROMPT}"


def iter_parts(response: Any) -> Iterable[Any]:
    parts = getattr(response, "parts", None)
    if parts:
        return parts

    candidates: list[Any] = getattr(response, "candidates", None) or []
    collected: list[Any] = []
    for candidate in candidates:
        content = getattr(candidate, "content", None)
        if content and getattr(content, "parts", None):
            collected.extend(content.parts)
    return collected


def extension_for_mime(mime_type: str) -> str:
    mapping = {
        "image/png": ".png",
        "image/jpeg": ".jpg",
        "image/webp": ".webp",
    }
    return mapping.get(mime_type, ".bin")


def generate_once(client: Any, spec: ImageSpec) -> tuple[str, Path]:
    LOGGER.info(
        "Requesting image: id=%s aspect_ratio=%s",
        spec.image_id,
        spec.aspect_ratio,
    )
    LOGGER.debug("Prompt preview for %s: %s", spec.image_id, build_prompt(spec)[:400])
    started_at = time.perf_counter()
    response: Any = client.models.generate_content(
        model=MODEL,
        contents=build_prompt(spec),
        config=types.GenerateContentConfig(
            response_modalities=["TEXT", "IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio=spec.aspect_ratio,
                image_size=IMAGE_SIZE,
            ),
        ),
    )
    elapsed = time.perf_counter() - started_at
    LOGGER.info("Response received for %s in %.2fs", spec.image_id, elapsed)

    text_parts: list[str] = []
    image_path: Path | None = None

    parts = list(iter_parts(response))
    LOGGER.debug("Response parts for %s: %d", spec.image_id, len(parts))

    for index, part in enumerate(parts, start=1):
        text = getattr(part, "text", None)
        if text:
            text_parts.append(text.strip())
            LOGGER.debug("Part %d for %s contains text", index, spec.image_id)
            continue

        inline_data = getattr(part, "inline_data", None)
        if inline_data is None:
            LOGGER.debug("Part %d for %s had no inline_data", index, spec.image_id)
            continue

        mime_type = getattr(inline_data, "mime_type", "image/png")
        data = getattr(inline_data, "data", None)
        if not data:
            LOGGER.debug("Part %d for %s had empty image data", index, spec.image_id)
            continue

        ext = extension_for_mime(mime_type)
        image_path = OUTPUT_DIR / f"{spec.image_id}{ext}"
        _ = image_path.write_bytes(bytes(data))
        LOGGER.info(
            "Saved image for %s: %s (%s)",
            spec.image_id,
            image_path,
            mime_type,
        )
        break

    if image_path is None:
        raise RuntimeError("No image was returned by Gemini.")

    response_text = "\n\n".join(part for part in text_parts if part)
    return response_text, image_path


def write_metadata(spec: ImageSpec, response_text: str, image_path: Path) -> None:
    metadata_path = OUTPUT_DIR / f"{spec.image_id}.json"
    metadata = {
        "model": MODEL,
        "image_size": IMAGE_SIZE,
        "image_path": str(image_path).replace("\\", "/"),
        "common_style_prompt": COMMON_STYLE_PROMPT,
        "spec": asdict(spec),
        "full_prompt": build_prompt(spec),
        "response_text": response_text,
    }
    _ = metadata_path.write_text(
        json.dumps(metadata, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    LOGGER.debug("Saved metadata for %s: %s", spec.image_id, metadata_path)


def generate_with_retry(
    client: Any, spec: ImageSpec, overwrite: bool
) -> tuple[bool, str]:
    existing = list(OUTPUT_DIR.glob(f"{spec.image_id}.*"))
    if existing and not overwrite:
        LOGGER.info("Skipping %s because output already exists", spec.image_id)
        return True, f"skip: {spec.image_id} (already exists)"

    last_error: Exception | None = None
    for attempt in range(1, RETRY_COUNT + 1):
        try:
            LOGGER.info(
                "Starting attempt %d/%d for %s",
                attempt,
                RETRY_COUNT,
                spec.image_id,
            )
            response_text, image_path = generate_once(client, spec)
            write_metadata(spec, response_text, image_path)
            LOGGER.info("Completed %s successfully", spec.image_id)
            return True, f"ok: {spec.image_id} -> {image_path}"
        except Exception as error:  # noqa: BLE001
            last_error = error
            LOGGER.exception(
                "Attempt %d/%d failed for %s",
                attempt,
                RETRY_COUNT,
                spec.image_id,
            )
            if attempt == RETRY_COUNT:
                break
            sleep_seconds = 2 ** attempt
            LOGGER.warning(
                "Retrying %s in %ss after error: %s",
                spec.image_id,
                sleep_seconds,
                error,
            )
            time.sleep(sleep_seconds)

    assert last_error is not None
    return False, f"failed: {spec.image_id} -> {last_error}"


def main() -> int:
    args = parse_args()
    configure_logging(args.verbose, args.debug)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    specs = select_specs(args.only)
    LOGGER.info("Output directory: %s", OUTPUT_DIR)
    LOGGER.info("Images selected: %s", ", ".join(spec.image_id for spec in specs))
    client = get_client()

    failures: list[str] = []
    for spec in specs:
        success, message = generate_with_retry(client, spec, overwrite=args.overwrite)
        print(message)
        if not success:
            failures.append(message)

    if failures:
        print("\nSome generations failed:", file=sys.stderr)
        for failure in failures:
            print(f"  - {failure}", file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
