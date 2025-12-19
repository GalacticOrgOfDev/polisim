"""File I/O operations for policy configuration import/export."""

import os
import io
import pandas as pd
from tkinter import filedialog, messagebox


def export_policy_to_csv(policy_data, file_path):
    """Export a policy configuration (general, revenues, outs) to CSV.
    
    Args:
        policy_data: Dict with 'general', 'revenues', 'outs' keys
        file_path: Path to save the CSV file
    """
    try:
        with open(file_path, 'w', newline='') as f:
            # General Parameters section
            f.write("[General Parameters]\n")
            general_df = pd.DataFrame(list(policy_data['general'].items()), columns=['Parameter', 'Value'])
            general_csv = general_df.to_csv(index=False)
            f.write(general_csv)
            if not general_csv.endswith('\n'):
                f.write('\n')
            f.write("\n")  # Blank line separator

            # Revenues section
            f.write("[Revenues]\n")
            if policy_data['revenues']:
                revenues_df = pd.DataFrame(policy_data['revenues'])
                revenues_csv = revenues_df.to_csv(index=False)
                f.write(revenues_csv)
                if not revenues_csv.endswith('\n'):
                    f.write('\n')
            else:
                f.write("name,is_percent,value,desc,alloc_health,alloc_states,alloc_federal\n")
            f.write("\n")  # Blank line separator

            # Expenditures section
            f.write("[Expenditures]\n")
            if policy_data['outs']:
                outs = []
                for out in policy_data['outs']:
                    # Flatten allocations into the main out record
                    base_out = {k:v for k,v in out.items() if k != 'allocations'}
                    for i, alloc in enumerate(out.get('allocations', [])):
                        base_out[f'alloc_{i+1}_source'] = alloc.get('source', '')
                        base_out[f'alloc_{i+1}_percent'] = alloc.get('percent', 0)
                    outs.append(base_out)
                outs_df = pd.DataFrame(outs)
                outs_csv = outs_df.to_csv(index=False)
                f.write(outs_csv)
                if not outs_csv.endswith('\n'):
                    f.write('\n')
            else:
                f.write("name,is_percent,value\n")
    except Exception as e:
        raise IOError(f"Failed to export policy: {str(e)}")


def import_policy_from_csv(file_path):
    """Import a policy configuration from CSV format.
    
    Args:
        file_path: Path to CSV file to import
    
    Returns:
        Dict with 'general', 'revenues', 'outs' keys
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Split by section headers
        sections = {}
        current_section = None
        section_lines = []

        for line in content.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('[') and line_stripped.endswith(']'):
                # Save previous section
                if current_section and section_lines:
                    sections[current_section] = '\n'.join([l for l in section_lines if l.strip()])
                current_section = line_stripped.strip('[]')
                section_lines = []
            elif current_section and line.strip():
                section_lines.append(line)

        # Save last section
        if current_section and section_lines:
            sections[current_section] = '\n'.join([l for l in section_lines if l.strip()])

        result = {}

        # Parse General Parameters
        if 'General Parameters' not in sections:
            raise ValueError("Missing 'General Parameters' section in CSV")

        general_df = pd.read_csv(io.StringIO(sections['General Parameters']))
        result['general'] = dict(zip(general_df['Parameter'], general_df['Value']))

        # Parse Revenues
        result['revenues'] = []
        if 'Revenues' in sections and sections['Revenues'].strip():
            revenues_df = pd.read_csv(io.StringIO(sections['Revenues']))
            result['revenues'] = revenues_df.to_dict('records')

        # Parse Expenditures
        result['outs'] = []
        if 'Expenditures' in sections and sections['Expenditures'].strip():
            outs_df = pd.read_csv(io.StringIO(sections['Expenditures']))
            for _, row in outs_df.iterrows():
                out = {
                    'name': row['name'],
                    'is_percent': row.get('is_percent', False),
                    'value': row['value'],
                    'allocations': []
                }
                # Reconstruct allocations from flattened columns
                i = 1
                while f'alloc_{i}_source' in row:
                    source = row[f'alloc_{i}_source']
                    percent = row.get(f'alloc_{i}_percent', 0)
                    if pd.notna(source) and source:
                        out['allocations'].append({'source': source, 'percent': percent})
                    i += 1
                result['outs'].append(out)

        return result
    except Exception as e:
        raise IOError(f"Failed to import policy: {str(e)}")


def export_results_to_file(current_df, proposed_df, summary_table, file_path, diff_table=None, normalized_table=None):
    """Export simulation results to file (Excel or CSV).

    Extended to accept optional `diff_table` and `normalized_table` which will be
    written as additional sheets in Excel output. CSV output will include them
    in a simple concatenated form.

    Args:
        current_df: DataFrame with current policy results
        proposed_df: DataFrame with proposed policy results
        summary_table: DataFrame with CBO summary metrics
        file_path: Path to save results
        diff_table: Optional DataFrame with differences vs baseline
        normalized_table: Optional DataFrame with per-capita / %GDP normalized metrics
    """
    try:
        if file_path.endswith('.xlsx'):
            with pd.ExcelWriter(file_path) as writer:
                if current_df is not None:
                    current_df.to_excel(writer, sheet_name='Current Policy', index=False)
                if proposed_df is not None:
                    proposed_df.to_excel(writer, sheet_name='Proposed Policy', index=False)
                # Add CBO-style summary as a sheet if available
                if summary_table is not None and not summary_table.empty:
                    summary_table.to_excel(writer, sheet_name='CBO Summary', index=False)
                # Add diff table and normalized table if provided
                if diff_table is not None and not diff_table.empty:
                    diff_table.to_excel(writer, sheet_name='Diff vs Baseline', index=False)
                if normalized_table is not None and not normalized_table.empty:
                    normalized_table.to_excel(writer, sheet_name='Normalized Per Capita', index=False)
        else:
            # For CSV, write summary first then combined data and append diffs/normalized
            with open(file_path, 'w', newline='') as f:
                if summary_table is not None and not summary_table.empty:
                    f.write('CBO-Style Summary\n')
                    summary_table.to_csv(f, index=False)
                    f.write('\n')

                f.write('Simulation Results\n')
                combined = pd.concat([
                    (current_df.assign(Policy='Current') if current_df is not None else pd.DataFrame()),
                    (proposed_df.assign(Policy='Proposed') if proposed_df is not None else pd.DataFrame())
                ], ignore_index=True)
                combined.to_csv(f, index=False)

                if diff_table is not None and not diff_table.empty:
                    f.write('\nDiff vs Baseline\n')
                    diff_table.to_csv(f, index=False)

                if normalized_table is not None and not normalized_table.empty:
                    f.write('\nNormalized Per Capita\n')
                    normalized_table.to_csv(f, index=False)
    except Exception as e:
        raise IOError(f"Failed to export results: {str(e)}")
