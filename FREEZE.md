# FREEZE: wexp_check code frozen before any corpus run

Every file below was hashed and committed before wexp_check was executed on any
WEXP test corpus. The comparison record (RUN-RECORD.json, comparison.json) was
added afterwards in a separate commit; this file is not changed by it.

## Files as committed (SHA-256, path)

```
210ec09e30335c52e74e852ecd90a7fd06aa24b0363fcaabce56a14059dcc8c3  DECISIONS.md
09bc89e91f1b304f2619944900d42a5c9ce49722c7a618eb1e3d5bfa41803166  FILES-READ.txt
cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30  LICENSE
399ca8202062a3fc33ca7898efd182644d6f56de626a8f912765cd603d654e62  README.md
3399dfce819678f06b936fe52537d862c72ed9ac790b328127287f101fb7fb79  pyproject.toml
e5a79a95058ed5f45305db90897bf6718e2eb3fc68c34915972a96431c65af4c  tests/fixtures/input/C01.json
07b586b78df7c891fd4ce1aa17d976be0f814f4aa5e870efe19aa599c1d880e9  tests/fixtures/profiles.json
5bb3e1bbe55421cd0de403a14ddcb5913993b6dd2e221854f108dc25a8f680e9  tests/test_wexp_check.py
ae4a9671e6bc22d8c3d591e36db00d1d0a069307fa1e0cf7afe030e0ddfe5a4a  wexp_check/__init__.py
6554ab7c151809297825d9af16e0463dac6c6cc176c4912bd4e011ba8f048120  wexp_check/__main__.py
d83ac0795f32b148acc45d924d9249647bc687b9f49f0f9658401f0cbc9e463e  wexp_check/core.py
2c8e9114ae25894853c9989fff37847d3f4f2afe7218ef68494d9506361eeab8  wexp_check/ingress.py
6e0c45e0ffddac18b7b7e6e4d0d28f39f08b98230243318b80794256b0db35ba  wexp_check/tokens.py
```

## Files as delivered by the isolated implementation session (SHA-256, path)

Three edits were made between delivery and this freeze, by the coordinator, not by
the implementation session. None changes the appraiser:

1. `FILES-READ.txt`: the absolute local directory prefix of every path was removed,
   leaving paths relative to the handoff directory. No line was added or removed.
2. `README.md`: one verb in the sentence stating what the appraiser does not do was
   changed from "certify" to "establish", so that the README contains none of the
   excluded words even in a negated form.
3. `tests/test_wexp_check.py`: the line that located the handoff directory relative
   to the test file (`HANDOFF = os.path.dirname(OUT)`) was replaced by
   `HANDOFF = os.path.join(HERE, "fixtures")` with a one-line comment, and the two
   handoff files the tests read, `input/C01.json` and `profiles.json`, were copied
   unchanged into `tests/fixtures/`. Without this the tests only ran inside the
   delivery directory. `OUT` (the package root used to run the command line) is kept.

All other files are byte-identical to the delivery.

```
210ec09e30335c52e74e852ecd90a7fd06aa24b0363fcaabce56a14059dcc8c3  DECISIONS.md
5f509f2404ec2e31f57045dee9b408a6be0736b603ce82f09a7e35565d4accd8  FILES-READ.txt
cfc7749b96f63bd31c3c42b5c471bf756814053e847c10f3eb003417bc523d30  LICENSE
260bf68d5fbf90c5cfa35af0f9dc64ce3cc2211bfde35d4fcf3096a36307bc36  README.md
3399dfce819678f06b936fe52537d862c72ed9ac790b328127287f101fb7fb79  pyproject.toml
ab2e8a9e8c5705c6ede7c3f659ded2c122a6c41092a33c2c0e225c8d8d32f598  tests/test_wexp_check.py
ae4a9671e6bc22d8c3d591e36db00d1d0a069307fa1e0cf7afe030e0ddfe5a4a  wexp_check/__init__.py
6554ab7c151809297825d9af16e0463dac6c6cc176c4912bd4e011ba8f048120  wexp_check/__main__.py
d83ac0795f32b148acc45d924d9249647bc687b9f49f0f9658401f0cbc9e463e  wexp_check/core.py
2c8e9114ae25894853c9989fff37847d3f4f2afe7218ef68494d9506361eeab8  wexp_check/ingress.py
6e0c45e0ffddac18b7b7e6e4d0d28f39f08b98230243318b80794256b0db35ba  wexp_check/tokens.py
```
