"""
PCB Data Consolidation Script
Consolidates PCB area statistics from segment CSV files into Excel template
"""

import pandas as pd
from openpyxl import load_workbook
from pathlib import Path
import sys

class PCBDataConsolidator:
    def __init__(self):
        # Use relative paths - files are in the same directory as the script
        self.source_excel = Path('01_CompositionPCBAdditionalInformation.xlsx')
        self.template_excel = Path('VehicleElectronicConsolidationData.xlsx')
        self.output_excel = Path('ConsolidatedVehicleElectronicPCBData.xlsx')
        
        # CSV segment files in PCBAreaMC subfolder
        self.csv_files = {
            'AB': Path('PCBAreaMC/csv_category/pcb_category_summary_AB_segment.csv'),
            'CD': Path('PCBAreaMC/csv_category/pcb_category_summary_CD_segment.csv'),
            'EF': Path('PCBAreaMC/csv_category/pcb_category_summary_EF_segment.csv')
        }
        
        self.source_df = None
        self.template_df = None
        self.csv_data = {}
        
    def validate_files(self):
        """Check if all required files exist"""
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
        
        # Check CSV files
        for segment, csv_path in self.csv_files.items():
            if csv_path.exists():
                print(f"✓ CSV {segment} segment found: {csv_path}")
            else:
                print(f"⚠ WARNING: CSV {segment} segment not found: {csv_path}")
        
        print("=" * 60)
        return True
    
    def load_data(self):
        """Load source Excel and CSV files"""
        print("\nLOADING DATA...")
        
        # Load source Excel
        print(f"Reading source Excel: {self.source_excel}")
        self.source_df = pd.read_excel(self.source_excel, sheet_name='ProductKey')
        print(f"✓ Loaded {len(self.source_df)} rows from source Excel")
        
        # Load template Excel
        print(f"Reading template Excel: {self.template_excel}")
        self.template_df = pd.read_excel(self.template_excel, sheet_name='Sheet1')
        print(f"✓ Loaded template Excel with {len(self.template_df.columns)} columns")
        
        # Load CSV files
        for segment, csv_path in self.csv_files.items():
            if csv_path.exists():
                self.csv_data[segment] = pd.read_csv(csv_path)
                print(f"✓ Loaded {segment} segment CSV with {len(self.csv_data[segment])} rows")
            else:
                print(f"⚠ Skipping missing {segment} segment CSV")
        
        print("=" * 60)
    
    def extract_segment_from_datafile(self, datafile):
        """Extract segment (AB, CD, EF) from datafile string"""
        if pd.isna(datafile):
            return None
        
        datafile_str = str(datafile)
        if 'AB_segment' in datafile_str:
            return 'AB'
        elif 'CD_segment' in datafile_str:
            return 'CD'
        elif 'EF_segment' in datafile_str:
            return 'EF'
        return None
    
    def get_statistics_from_csv(self, segment, category):
        """Get statistics for a specific segment and category"""
        if segment not in self.csv_data:
            return None
        
        csv_df = self.csv_data[segment]
        
        # Find the row with matching category
        category_row = csv_df[csv_df['Category'] == category]
        
        if category_row.empty:
            return None
        
        # Extract _Total_Area statistics
        stats = {
            'mean': category_row['Mean_Total_Area'].values[0],
            'median': category_row['Median_Total_Area'].values[0],
            'mode': category_row['Mode_Total_Area'].values[0],
            'std': category_row['Std_Total_Area'].values[0],
            'p025': category_row['P025_Total_Area'].values[0],
            'p975': category_row['P975_Total_Area'].values[0]
        }
        
        return stats
    
    def process_all_rows(self):
        """Process all rows from source Excel"""
        print("\nPROCESSING DATA...")
        print("=" * 60)
        
        # Create output dataframe by copying template structure
        output_rows = []
        
        total_rows = len(self.source_df)
        success_count = 0
        skip_count = 0
        
        for idx, source_row in self.source_df.iterrows():
            # Extract segment and category
            segment = self.extract_segment_from_datafile(source_row['datafile'])
            category = source_row['category']
            
            print(f"\nRow {idx + 1}/{total_rows}: Segment={segment}, Category={category}")
            
            if not segment:
                print(f"  ⚠ Warning: Could not determine segment, skipping")
                skip_count += 1
                continue
            
            if segment not in self.csv_data:
                print(f"  ⚠ Warning: CSV data for segment {segment} not loaded, skipping")
                skip_count += 1
                continue
            
            # Get statistics from CSV
            stats = self.get_statistics_from_csv(segment, category)
            
            if not stats:
                print(f"  ⚠ Warning: Could not find statistics for category {category} in segment {segment}")
            else:
                print(f"  ✓ Statistics found: Mean={stats['mean']:.2f}, STD={stats['std']:.2f}")
            
            # Create output row - start with source data
            output_row = {}
            
            # Copy all matching columns from source
            for col in source_row.index:
                if col not in ['datafile', 'category']:  # Skip internal lookup columns
                    output_row[col] = source_row[col]
            
            # Add statistics from CSV
            if stats:
                output_row['meanValue'] = stats['mean']
                output_row['medianValue'] = stats['median']
                output_row['modeValue'] = stats['mode']
                output_row['STD'] = stats['std']
                output_row['p025'] = stats['p025']
                output_row['p975'] = stats['p975']
                output_row['uncertaintyValue (Remark: same unit as the value)'] = 2 * stats['std']
            else:
                output_row['meanValue'] = 'N/A'
                output_row['medianValue'] = 'N/A'
                output_row['modeValue'] = 'N/A'
                output_row['STD'] = 'N/A'
                output_row['p025'] = 'N/A'
                output_row['p975'] = 'N/A'
                output_row['uncertaintyValue (Remark: same unit as the value)'] = 'N/A'
            
            # Add missing hierarchy levels with N/A
            output_row['productKeyLevel3'] = 'N/A'
            output_row['componentKeyLevel3'] = 'N/A'
            output_row['componentKeyLevel4'] = 'N/A'
            output_row['componentKeyLevel5'] = 'N/A'
            output_row['materialKeyLevel3'] = 'N/A'
            output_row['materialKeyLevel4'] = 'N/A'
            
            # Handle reference, DOI, NDA - set N/A if empty
            if pd.isna(output_row.get('reference')) or output_row.get('reference') == '':
                output_row['reference'] = 'N/A'
            if pd.isna(output_row.get('DOI')) or output_row.get('DOI') == '':
                output_row['DOI'] = 'N/A'
            if pd.isna(output_row.get('NDA (yes/no)')) or output_row.get('NDA (yes/no)') == '':
                output_row['NDA (yes/no)'] = 'N/A'
            
            # Handle notes, dataProcessor, dataProcessorInstitution, dataEntryDate - set N/A if empty
            if pd.isna(output_row.get('notes')) or output_row.get('notes') == '':
                output_row['notes'] = 'N/A'
            if pd.isna(output_row.get('dataProcessor')) or output_row.get('dataProcessor') == '':
                output_row['dataProcessor'] = 'N/A'
            if pd.isna(output_row.get('dataProcessorInstitution')) or output_row.get('dataProcessorInstitution') == '':
                output_row['dataProcessorInstitution'] = 'N/A'
            if pd.isna(output_row.get('dataEntryDate')) or output_row.get('dataEntryDate') == '':
                output_row['dataEntryDate'] = 'N/A'
            
            # Update path with prefix
            if pd.notna(source_row['path']):
                output_row['path'] = f"/PCBAreaMC{source_row['path']}"
            else:
                output_row['path'] = 'N/A'
            
            output_rows.append(output_row)
            success_count += 1
        
        # Create output DataFrame with template columns
        self.output_df = pd.DataFrame(output_rows, columns=self.template_df.columns)
        
        print("\n" + "=" * 60)
        print(f"PROCESSING COMPLETE")
        print(f"  Total rows: {total_rows}")
        print(f"  Successfully processed: {success_count}")
        print(f"  Skipped: {skip_count}")
        print("=" * 60)
    
    def save_output(self):
        """Save the consolidated workbook"""
        print(f"\nSaving output to: {self.output_excel}")
        
        # Save to Excel
        self.output_df.to_excel(self.output_excel, sheet_name='Sheet1', index=False)
        print(f"✓ Output saved successfully!")
        print("=" * 60)
    
    def run(self):
        """Main execution method"""
        print("\n" + "=" * 60)
        print("PCB DATA CONSOLIDATION SCRIPT")
        print("=" * 60)
        
        # Step 1: Validate files
        if not self.validate_files():
            print("\nERROR: File validation failed. Exiting.")
            return False
        
        # Step 2: Load data
        try:
            self.load_data()
        except Exception as e:
            print(f"\nERROR loading data: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 3: Process all rows
        try:
            self.process_all_rows()
        except Exception as e:
            print(f"\nERROR processing data: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Step 4: Save output
        try:
            self.save_output()
        except Exception as e:
            print(f"\nERROR saving output: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        print("\n✓ ✓ ✓ CONSOLIDATION COMPLETED SUCCESSFULLY! ✓ ✓ ✓\n")
        return True


if __name__ == '__main__':
    consolidator = PCBDataConsolidator()
    success = consolidator.run()
    sys.exit(0 if success else 1)