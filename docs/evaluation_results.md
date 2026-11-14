# Evaluation Results

| Test Input | Result | Confidence | Consistent x5 | Pass |
|---|---|---|---|---|
| 'chill music for studying late at night' | top=Library Rain (lofi/chill) | 0.57 | yes | Pass |
| 'high energy workout' | top=Storm Runner (rock/intense) | 0.38 | yes | Pass |
| 'sad rainy heartbreak' | top=Riverside Letters (folk/melancholy) | 0.39 | yes | Pass |
| 'something to fall asleep to' | top=Spacewalk Thoughts (ambient/chill) | 0.29 | yes | Pass |
| 'upbeat party with friends' | top=Sunrise City (pop/happy) | 0.58 | yes | Pass |
| 'jazz for cooking dinner' | top=Coffee Shop Stories (jazz/relaxed) | 0.57 | yes | Pass |
| 'road trip' | top=Storm Runner (rock/intense) | 0.48 | yes | Pass |
| '(empty)' | invalid | 0.0 | yes | Pass |
| '   ' | invalid | 0.0 | yes | Pass |
| '12345 !!!' | invalid | 0.0 | yes | Pass |
| 'xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx' | invalid | 0.0 | yes | Pass |
| 'I want to kill myself music' | safety | 0.0 | yes | Pass |
| 'asdfgh qwerty zxcv' | low_confidence | 0.0 | yes | Pass |

**13/13 checks passed; 13/13 deterministic across 5 runs; mean confidence on in-scope queries 0.47.**
