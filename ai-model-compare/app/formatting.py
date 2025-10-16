from __future__ import annotations

import re

_SINGLE_LINE_WHITESPACE = re.compile(r"\s+")


def normalize_single_line(text: str) -> str:
	 if not text:
		 return ""
	 # collapse whitespace and strip
	 line = _SINGLE_LINE_WHITESPACE.sub(" ", text)
	 return line.replace("\n", "").replace("\r", "").strip()
