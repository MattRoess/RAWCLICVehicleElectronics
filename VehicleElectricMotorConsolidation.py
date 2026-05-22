"""
Electric Motor Data Consolidation Script
Consolidates material mass statistics from a single summary CSV into Excel template
"""

import pandas as pd
from pathlib import Path
import sys


# Segment mapping: productKeyLevel2 → segment group
SEGMENT_MAP = {
    'V0301030000': 'CD',
    'V0301030101': 'AB',
    'V0301030102': 'AB',
    'V0301030103': 'CD',
    'V0301030104': 'CD',
    'V0301030105': 'EF',
    'V0301030106': 'EF',
    'V0301030201': 'AB',
    'V0301030202': 'AB',
    'V0301030203': 'CD',
    'V0301030204': 'CD',
    'V0301030205': 'EF',
    'V0301030206': 'EF',
}


class ElectricMotorDataConsolidator:
    def __init__(self):
        self.source_excel   = Path('02_CompositionElectricMotorsAdditionalInformation.xlsx')
        self.template_excel = Path('VehicleElectronicConsolidationData.xlsx')
        self.output_excel   = Path('ConsolidatedVehicleElectronicElectricalMotorData.xlsx')

        # Single combined summary CSV for all segments
        self.csv_file = Path('ElectricMotorMC/materials_summary_csv/materials_mc_summary.csv')

        self.source_df   = None
        self.template_df = None
        self.csv_df      = None

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    def validate_files(self):
        print("=" * 60)
        print("VALIDATING INPUT FILES")
        print("=" * 60)

        if not self.source_excel.exists():
            print(f"ERROR: Source Excel not found: {self.source_excel}")
            return False
        print(f"✓ Source Excel found: {self.source_excel}")

        if not self.template_excel.exists():
            print(f"ERROR: Template Excel not found: {self.template_excel}")
            return False
        print(f"✓ Template Excel found: {self.template_excel}")

        if not self.csv_file.exists():
            print(f"ERROR: Summary CSV not found: {self.csv_file}")
            return False
        print(f"✓ Summary CSV found: {self.csv_file}")

        print("=" * 60)
        return True

    # ------------------------------------------------------------------
    # Loading
    # ------------------------------------------------------------------
    def load_data(self):
        print("\nLOADING DATA...")

        print(f"Reading source Excel: {self.source_excel}")
        self.source_df = pd.read_excel(self.source_excel, sheet_name='ProductKey')
        print(f"✓ Loaded {len(self.source_df)} rows from source Excel")

        print(f"Reading template Excel: {self.template_excel}")
        self.template_df = pd.read_excel(self.template_excel, sheet_name='Sheet1')
        print(f"✓ Loaded template Excel with {len(self.template_df.columns)} columns")

        print(f"Reading summary CSV: {self.csv_file}")
        self.csv_df = pd.read_csv(self.csv_file)
        print(f"✓ Loaded summary CSV with {len(self.csv_df)} rows")
        print(f"  CSV columns: {list(self.csv_df.columns)}")

        print("=" * 60)

    # ------------------------------------------------------------------
    # Segment lookup
    # ------------------------------------------------------------------
    def extract_segment(self, product_key_level2):
        """Return segment group for a given productKeyLevel2 value."""
        if pd.isna(product_key_level2):
            return None
        return SEGMENT_MAP.get(str(product_key_level2), None)

    # ------------------------------------------------------------------
    # Statistics lookup
    # CSV columns: 'Segment'  → segment group (AB / CD / EF)
    #              'Motor'    → source column 'category0'
    #              'Material' → source column 'category1'
    # ------------------------------------------------------------------
    def get_statistics_from_csv(self, segment, motor, material):
        """Return mass statistics for the matching Segment + Motor + Material row."""
        mask = (
            (self.csv_df['Segment']  == segment) &
            (self.csv_df['Motor']    == motor)   &
            (self.csv_df['Material'] == material)
        )
        matched = self.csv_df[mask]

        if matched.empty:
            return None

        row = matched.iloc[0]
        return {
            'mean':   row['Mean_mass_kg'],
            'median': row['Median_mass_kg'],
            'mode':   row['Mode_mass_kg'],
            'std':    row['Std_mass_kg'],
            'p025':   row['P025_mass_kg'],
            'p975':   row['P975_mass_kg'],
        }

    # ------------------------------------------------------------------
    # Helper
    # ------------------------------------------------------------------
    def _set_na_if_empty(self, d, key):
        val = d.get(key)
        if val is None or val == '' or (isinstance(val, float) and pd.isna(val)):
            d[key] = 'N/A'

    # ------------------------------------------------------------------
    # Processing
    # ------------------------------------------------------------------
    def process_all_rows(self):
        print("\nPROCESSING DATA...")
        print("=" * 60)

        output_rows   = []
        total_rows    = len(self.source_df)
        success_count = 0
        skip_count    = 0

        for idx, source_row in self.source_df.iterrows():
            product_key = source_row['productKeyLevel2']
            segment     = self.extract_segment(product_key)
            motor       = source_row['category0']    # → CSV column 'Motor'
            material    = source_row['category1']    # → CSV column 'Material'

            print(f"\nRow {idx + 1}/{total_rows}: "
                  f"ProductKey={product_key}, Segment={segment}, "
                  f"Motor={motor}, Material={material}")

            if not segment:
                print(f"  ⚠ Warning: No segment mapping for productKeyLevel2='{product_key}', skipping")
                skip_count += 1
                continue

            stats = self.get_statistics_from_csv(segment, motor, material)

            if stats:
                print(f"  ✓ Statistics found: Mean={stats['mean']:.4f}, STD={stats['std']:.4f}")
            else:
                print(f"  ⚠ Warning: No row found for Segment='{segment}', "
                      f"Motor='{motor}', Material='{material}'")

            output_row = {}

            # --- Passthrough columns (copied directly from source) --------
            passthrough_cols = [
                'dataEntryID', 'relatedRawclic-WS', 'Technology',
                'productKeyLevel1', 'productKeyLevel2',
                'productionYear',
                'componentKeyLevel0', 'componentKeyLevel1', 'componentKeyLevel2',
                'materialKeyLevel0', 'materialKeyLevel1', 'materialKeyLevel2', 'materialKeyLevel3',
                'parameterCode', 'parameter',
                'valueGeneration', 'dataSetType',
                'dqValidity', 'dqAccuracy', 'dqIntegrity', 'dqTimeliness', 'dqCompleteness',
                'reference', 'DOI', 'NDA (yes/no)',
                'notes', 'dataProcessor', 'dataProcessorInstitution', 'dataEntryDate',
            ]
            for col in passthrough_cols:
                if col in source_row.index:
                    output_row[col] = source_row[col]

            # --- Hierarchy levels absent in source → N/A ------------------
            output_row['productKeyLevel3']   = 'N/A'
            output_row['componentKeyLevel3'] = 'N/A'
            output_row['componentKeyLevel4'] = 'N/A'
            output_row['componentKeyLevel5'] = 'N/A'
            output_row['materialKeyLevel4']  = 'N/A'

            # --- Statistics from CSV --------------------------------------
            if stats:
                output_row['meanValue']   = stats['mean']
                output_row['medianValue'] = stats['median']
                output_row['modeValue']   = stats['mode']
                output_row['STD']         = stats['std']
                output_row['p025']        = stats['p025']
                output_row['p975']        = stats['p975']
                output_row['uncertaintyValue (Remark: same unit as the value)'] = 2 * stats['std']
            else:
                for col in ('meanValue', 'medianValue', 'modeValue', 'STD', 'p025', 'p975',
                            'uncertaintyValue (Remark: same unit as the value)'):
                    output_row[col] = 'N/A'

            # --- Optional string fields → N/A if empty --------------------
            for key in ('reference', 'DOI', 'NDA (yes/no)', 'notes',
                        'dataProcessor', 'dataProcessorInstitution', 'dataEntryDate'):
                self._set_na_if_empty(output_row, key)

            # --- Path with prefix -----------------------------------------
            if pd.notna(source_row.get('path')):
                output_row['path'] = f"/ElectricMotorMC{source_row['path']}"
            else:
                output_row['path'] = 'N/A'

            output_rows.append(output_row)
            success_count += 1

        # Align to template column order
        self.output_df = pd.DataFrame(output_rows, columns=self.template_df.columns)

        print("\n" + "=" * 60)
        print("PROCESSING COMPLETE")
        print(f"  Total rows:             {total_rows}")
        print(f"  Successfully processed: {success_count}")
        print(f"  Skipped:                {skip_count}")
        print("=" * 60)

    # ------------------------------------------------------------------
    # Save
    # ------------------------------------------------------------------
    def save_output(self):
        print(f"\nSaving output to: {self.output_excel}")
        self.output_df.to_excel(self.output_excel, sheet_name='Sheet1', index=False)
        print("✓ Output saved successfully!")
        print("=" * 60)

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def run(self):
        print("\n" + "=" * 60)
        print("ELECTRIC MOTOR DATA CONSOLIDATION SCRIPT")
        print("=" * 60)

        if not self.validate_files():
            print("\nERROR: File validation failed. Exiting.")
            return False

        try:
            self.load_data()
        except Exception as e:
            print(f"\nERROR loading data: {e}")
            import traceback; traceback.print_exc()
            return False

        try:
            self.process_all_rows()
        except Exception as e:
            print(f"\nERROR processing data: {e}")
            import traceback; traceback.print_exc()
            return False

        try:
            self.save_output()
        except Exception as e:
            print(f"\nERROR saving output: {e}")
            import traceback; traceback.print_exc()
            return False

        print("\n✓ ✓ ✓ CONSOLIDATION COMPLETED SUCCESSFULLY! ✓ ✓ ✓\n")
        return True


if __name__ == '__main__':
    consolidator = ElectricMotorDataConsolidator()
    success = consolidator.run()
    sys.exit(0 if success else 1)