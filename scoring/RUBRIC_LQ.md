# Language-quality rubric (Hindi and Hinglish answers)

You are scoring the LANGUAGE of customer-support answers, as a fluent everyday Hindi speaker in India would judge it. Do not judge whether the answer is factually right, complete or helpful.

- 2 = reads as if a fluent Hindi (or Hinglish) support agent wrote it: natural, clear, everyday wording.
- 1 = understandable, but stiff, bookish or translated-sounding; or has grammar/gender errors, odd word choice, stray characters from other scripts, or a noticeably awkward mix.
- 0 = hard to follow for an ordinary speaker, garbled, or not Hindi/Hinglish at all.

Calibration from the native-speaker reviewer (from his notes on a separate calibration set):
- Plain, simple Hindi that is easy to read is what earns a 2. A well-structured answer in pure Hindi can also be a 2.
- Heavily formal, Sanskritised or "official translation" Hindi that an everyday colloquial speaker would find hard to read is marked down, to 1 or even 0. Stiff written-register phrases (for example "उपरोक्त चरणों") cost a point.
- Names of on-screen buttons and menus (Settings, Devices, Deregister) are better left in English, since that is how the customer sees them. Ordinary English loanwords (app, device, download, password) are normal in Hindi.
- Script alone is not penalised: if the question is Hinglish (Hindi in Latin letters) and the answer is in Devanagari, or the reverse, score the language as written. But an answer that is essentially English gets 0.
- For Hinglish answers: natural Hinglish as people actually type it earns 2; Hinglish that is really formal Hindi transliterated, or that is clumsy or inconsistent, earns 1.

Output: one line per answer, exactly `item|score|short reason` (score is 0, 1 or 2).
