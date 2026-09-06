import io
import logging

import pandas as pd

logger = logging.getLogger(__name__)


def parse_file(file_bytes: bytes, filename: str) -> dict:
    """Parse CSV or Excel file, return metadata + markdown table (first 200 rows)."""
    ext = filename.rsplit(".", 1)[-1].lower()

    logger.info("parse_file: filename=%s, size=%d bytes", filename, len(file_bytes))

    if ext == "csv":
        df = pd.read_csv(io.BytesIO(file_bytes))
    elif ext in ("xlsx", "xls"):
        df = pd.read_excel(io.BytesIO(file_bytes))
    else:
        raise ValueError(f"Неподдерживаемый формат файла: .{ext}. Используйте CSV или Excel.")

    if df.empty:
        raise ValueError("Файл пустой — нет данных для анализа.")

    total_rows = len(df)
    df_preview = df.head(200)

    logger.info(
        "parse_file: rows=%d, columns=%d (%s)",
        total_rows,
        len(df.columns),
        ", ".join(df.columns.astype(str)),
    )

    metadata = (
        f"Файл: {filename}\n"
        f"Всего строк: {total_rows}\n"
        f"Колонки ({len(df.columns)}): {', '.join(df.columns.astype(str))}\n"
        f"Типы данных: {', '.join(f'{col}={dtype}' for col, dtype in df.dtypes.items())}\n"
    )

    table_md = df_preview.to_markdown(index=False)

    return {
        "table_data": f"{metadata}\n\nДанные таблицы (первые {len(df_preview)} строк из {total_rows}):\n\n{table_md}",
        "preview": df_preview.head(10).to_dict(orient="records"),
        "total_rows": total_rows,
        "columns": list(df.columns.astype(str)),
    }
