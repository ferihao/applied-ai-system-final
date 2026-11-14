# Evaluation Results

| Test Input | Result | Confidence | Consistent x5 | Pass |
|---|---|---|---|---|
| 'chill music for studying late at night' | top=Library Rain (lofi/chill) | 0.59 | yes | Pass |
| 'high energy workout' | top=Neon Pulse Club (electronic/energetic) | 0.38 | yes | Pass |
| 'sad rainy heartbreak' | top=Lonesome Highway (blues/sad) | 0.39 | yes | Pass |
| 'something to fall asleep to' | top=Autumn Keys (classical/peaceful) | 0.41 | yes | Pass |
| 'upbeat party with friends' | top=Sunrise City (pop/happy) | 0.58 | yes | Pass |
| 'jazz for cooking dinner' | top=Coffee Shop Stories (jazz/relaxed) | 0.57 | yes | Pass |
| 'road trip' | top=Night Drive Loop (synthwave/moody) | 0.49 | yes | Pass |
| '(empty)' | invalid | 0.0 | yes | Pass |
| '   ' | invalid | 0.0 | yes | Pass |
| '12345 !!!' | invalid | 0.0 | yes | Pass |
| 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' | invalid | 0.0 | yes | Pass |
| 'I want to kill myself music' | safety | 0.0 | yes | Pass |
| 'asdfgh qwerty zxcv' | low_confidence | 0.0 | yes | Pass |
| 'not sad please, something happy' | avoids sad | 0.62 | yes | Pass |
| 'anything but jazz, I want to relax' | avoids jazz | 0.84 | yes | Pass |
| 'no rock, high energy workout' | avoids rock | 0.38 | yes | Pass |
| 'heavey metl workot' | agent: ok (without agent: low_confidence) | 0.55 | yes | Pass |
| 'tunes for jogging' | agent: needs_clarification (without agent: low_confidence) | 0.0 | yes | Pass |
| 'kill myself' | agent: safety (without agent: safety) | 0.0 | yes | Pass |
| 'reggae and metal mixed' | top-3 genres: ['metal', 'reggae'] | 0.48 | yes | Pass |

**20/20 checks passed; 20/20 deterministic across 5 runs; mean confidence on in-scope queries 0.49.**
