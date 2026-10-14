# Tensile Analyzer

A Python desktop tool for engineering stress-strain analysis of thin-film tensile tests.

Select CSV files or a folder, enter specimen width, thickness and gauge length in mm, then export one editable Excel workbook. Each CSV represents one sample with multiple trials in repeating time (s), force (N), stroke (mm) columns and three header rows. UTF-8 and CP932 are supported.

## Run

Install Python 3.12 or later, run `python -m pip install -r requirements.txt`, then `python tensile_gui.py`.

Width defaults to 4 mm and gauge length to 20 mm. Thickness is required. Double-click a sample to edit its dimensions. The modulus fit range defaults to 0.05-0.25% strain and uses linear regression with a free intercept. Modulus is reported in GPa.

Fracture detection looks for a 50% stress drop within 0.1 s, confirmed by 3-5 low points. The last local high point before that decline is used as fracture. The threshold is editable. A minimum of 20% of the trial's maximum stress prevents low-load noise triggering detection. Missing fracture results are left blank. Manual fracture strain overrides are available per trial. Toughness integrates raw engineering stress against dimensionless strain up to fracture, in MJ/m3. No preload, zero, compliance or toe correction is applied. Strain is calculated from machine stroke, not an extensometer.

Smoothing uses Savitzky-Golay (11 points, order 3) for plots only. All metrics use raw data. The representative curve is the trial whose tensile strength is closest to the sample mean. Standard deviations are sample SD (n-1); SD is blank for one trial.

The workbook contains Properties (dual-axis bars with SD), Stress_Strain (representative curves), Summary (trial metrics and sample statistics), and a data/fit sheet for each trial. All charts are editable Excel objects. Changes to settings require rerunning the analysis.

Developed with AI assistance. Experimental data are excluded from this repository.
