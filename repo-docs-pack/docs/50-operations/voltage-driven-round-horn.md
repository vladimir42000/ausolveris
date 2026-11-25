# Voltage-driven round horn — development checkpoint

Base: AuSolveris PR #7 at b86d4a91ce2c5ef5a00bc4370d0cecb040779bd7. Branch: dev/voltage-driven-round-horn. Compatible kernel: vladimir42000/os-lem at 9489f1941cc64abac8bad2dc4f2fb86c697a91b3.

The example uses OS-LEM's coupled driver matrix, terminates the front with the complex FEM horn impedance and fixes rear pressure to zero. Electrical and mechanical equations come from the kernel. All exported phasors use exp(-i omega t) and RMS amplitudes. The direct rigid diaphragm has the same area as the throat. The motor is an illustrative linear fixture; its parameters do not characterize a commercial compression driver.

## Reproduce

From the AuSolveris branch in a virtual environment with Git access:

```sh
python -m pip install -r requirements.txt
python -m pip install 'git+https://github.com/vladimir42000/os-lem.git@9489f1941cc64abac8bad2dc4f2fb86c697a91b3'
export OPENBLAS_NUM_THREADS=1 PYTHONPATH=src
python -m unittest discover -s tests/geometry -p test_driven_round_horn.py -v
python examples/round_horn_one_volt.py > horn-1v.csv
```

The CSV contains 135 observations on the 1 m arc (0 to 88 degrees in 2-degree steps). On-axis results:

| Hz | Axial x radial cells | Input impedance, ohm | SPL at 1 m, dB re 20 µPa |
|---:|---:|---:|---:|
| 1000 | 96 x 16 | 6.116735 + 0.685931i | 76.31745 |
| 6000 | 192 x 32 | 6.003398 - 3.557607i | 75.09428 |
| 30000 | 768 x 128 | 6.000136 - 18.807114i | 57.72575 |

Three new unittest cases passed with the pinned kernel. Four existing round-horn regression functions also passed when executed directly. The full repository suite has yet to run on this branch. The independent circuit oracle checks complex electrical impedance. Mouth power integrated from annular FEM pressure and velocity closes the electrical power balance at 1 and 6 kHz. A second FEM solve checks peak-to-RMS complex microphone pressure scaling.

## Resume here

Run the complete AuSolveris suite with the pinned kernel installed and confirm the three coupling tests execute. Add a benchmark with a known rear load and a frequency sweep around the loaded resonance. Real compression-driver modelling also needs a defined diaphragm-to-throat transfer or phase plug. Independent full-horn validation against matched AKABAK results or measurements remains open.
