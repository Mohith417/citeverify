class UploadError(Exception):
    def __init__(self, status_code: int, message: str):
        self.status_code = status_code
        self.message = message
        super().__init__(message)


def read_limited(fileobj, max_bytes: int) -> bytes:
    # read in chunks so an oversized upload is rejected without loading it all
    chunks, total = [], 0
    while True:
        chunk = fileobj.read(1024 * 1024)
        if not chunk:
            break
        total += len(chunk)
        if total > max_bytes:
            raise UploadError(413, f"File too large (limit {max_bytes // (1024 * 1024)} MB).")
        chunks.append(chunk)
    return b"".join(chunks)


def validate_pdf(filename: str | None, data: bytes) -> None:
    if not filename or not filename.lower().endswith(".pdf"):
        raise UploadError(400, "Only .pdf files are accepted.")
    if not data:
        raise UploadError(400, "The uploaded file is empty.")
    if not data.lstrip()[:5] == b"%PDF-":
        raise UploadError(400, "File is not a valid PDF (missing PDF header).")
