# Tensile Analyzer

A Python desktop tool for engineering stress-strain analysis of thin-film tensile tests.

Select CSV files or a folder, enter specimen width, thickness and gauge length in mm, then export one editable Excel workbook. Each CSV represents one sample with multiple trials in repeating time (s), force (N), stroke (mm) columns and three header rows. UTF-8 and CP932 are supported.

## Run

Install Python 3.12 or later, run `python -m pip install -r requirements.txt`, then `python tensile_gui.py`.

Width defaults to 4 mm and gauge length to 20 mm; both are common to all samples. The sample list has a fixed height and a vertical scrollbar. Each sample has its own thickness, trial selector and modulus fit limits (default 0.05-0.25% strain). All selected curves appear together, with each fitting interval drawn thicker. Mean strength, modulus and detected fracture strain appear beside each sample. Changing sample settings updates the curves and statistics automatically. The initial trial is closest to mean maximum force. The preview includes the post-fracture tail and creates no output files. Click Run to generate Excel using each sample's fitting limits. Modulus uses linear regression with a free intercept, in GPa.

The Run button stays in the top toolbar. Open **Details** beside a sample to view all its trial curves, individual results and source time/force/stroke data. Trial thickness and fit limits can override sample defaults; blank fields inherit the sample settings. **Include in mean** controls whether a trial contributes to sample means, SD and automatic representative selection. Excluded trials remain in the workbook, with their inclusion status recorded. Edits are retained while the application is open, including after closing and reopening Details. They are not saved across application restarts.

Details displays live means for included trials. **Plot shift (%)** moves an individual curve horizontally in strain percentage points (positive right, negative left), including its highlighted fitting segment. It changes display coordinates only; original strain, fitted modulus and all metrics are unchanged. Excel retains original strain alongside shifted plotting strain. **Show in SS** controls whether a sample appears in the main/Excel stress-strain overview and does not exclude it from statistics. Excel panes are unfrozen, axes use automatic numeric formatting without a trailing decimal point, and error bars have end caps.

The sample-level Plot shift moves every trial in that sample; it adds to each trial's individual shift. The minus/plus buttons change the value by 0.01 percentage points and repeat when held. Details supports vertical scrolling over its trial table. **Clear imported data** removes loaded samples and edits from the current session without deleting files. Export skips samples whose sample-level thickness is blank and lists their names; at least one sample needs a valid thickness. Sheet 1 has no legend and Sheet 2 places its legend at the top.

Fracture detection looks for a 50% stress drop within 0.1 s, confirmed by 3-5 low points. The last local high point before that decline is used as fracture. The threshold is editable. A minimum of 20% of the trial's maximum stress prevents low-load noise triggering detection. Missing fracture results are left blank. Manual fracture strain overrides are available per trial. Toughness integrates raw engineering stress against dimensionless strain up to fracture, in MJ/m3. No preload, zero, compliance or toe correction is applied. Strain is calculated from machine stroke, not an extensometer.

Smoothing uses Savitzky-Golay (11 points, order 3) for plots only. All metrics use raw data. The representative curve is the trial whose tensile strength is closest to the sample mean. Standard deviations are sample SD (n-1); SD is blank for one trial.

The workbook contains Properties (paired dual-axis bars with SD), Stress_Strain (representative curves), Summary (all trial metrics, inclusion flags and sample statistics), and a data/fit sheet for each trial. Means and SD use included trials only; missing fracture values are omitted for fracture-related statistics. If no trials are included, the sample mean is blank. All charts are editable Excel objects, sized 5 by 5 inches with a 4 by 4 inch plot area, Arial 14 pt labels, black 1 pt borders and no gridlines. The selected eligible representative trial is used for Excel; otherwise the included trial closest to the mean strength is selected. Changes to settings require rerunning the analysis.

Developed with AI assistance. Experimental data are excluded from this repository.
