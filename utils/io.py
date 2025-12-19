"""File I/O operations for policy configuration import/export.

Provides utilities for:
- Exporting policies to CSV/Excel format
- Importing policies from CSV/Excel
- Exporting simulation results
- Handling JSON/YAML scenario files
"""

import os
import io
import json
import logging
import pandas as pd
from pathlib import Path
from typing import Dict, Optional, Any

logger = logging.getLogger(__name__)


def export_policy_to_csv(policy_data: Dict, file_path: str) -> None:
    """Export a policy configuration to CSV format.
    
    Args:
        policy_data: Dict with 'general', 'revenues', 'outs' keys
        file_path: Path to save the CSV file
    
    Raises:
        IOError: If file writing fails
        ValueError: If policy_data structure is invalid
    """
    logger.info(f"Exporting policy to CSV: {file_path}")
    
    try:
        # Validate input
        if not isinstance(policy_data, dict):
            raise ValueError("policy_data must be a dictionary")
        if 'general' not in policy_data or 'revenues' not in policy_data or 'outs' not in policy_data:
            raise ValueError("policy_data must have 'general', 'revenues', 'outs' keys")
        
        with open(file_path, 'w', newline='', encoding='utf-8') as f:
            # General Parameters section
            f.write("[General Parameters]\n")
            general_df = pd.DataFrame(list(policy_data['general'].items()), columns=['Parameter', 'Value'])
            general_csv = general_df.to_csv(index=False)
            f.write(general_csv)
            if not general_csv.endswith('\n'):
                f.write('\n')
            f.write("\n")  # Blank line separator
            logger.debug(f"Exported {len(general_df)} general parameters")

            # Revenues section
            f.write("[Revenues]\n")
            if policy_data['revenues']:
                revenues_df = pd.DataFrame(policy_data['revenues'])
                revenues_csv = revenues_df.to_csv(index=False)
                f.write(revenues_csv)
                if not revenues_csv.endswith('\n'):
                    f.write('\n')
                logger.debug(f"Exported {len(revenues_df)} revenue sources")
            else:
                f.write("name,is_percent,value,desc,alloc_health,alloc_states,alloc_federal\n")
                logger.debug("No revenue sources to export")
            f.write("\n")

            # Expenditures section
            f.write("[Expenditures]\n")
            if policy_data['outs']:
                outs = []
                for out in policy_data['outs']:
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
                logger.debug(f"Exported {len(outs_df)} spending categories")
            else:
                f.write("name,is_percent,value\n")
                logger.debug("No spending categories to export")
        
        logger.info(f"✓ Policy exported successfully to {file_path}")
        
    except IOError as e:
        logger.error(f"File I/O error while exporting policy: {e}")
        raise IOError(f"Failed to export policy: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while exporting policy: {e}")
        raise IOError(f"Failed to export policy: {str(e)}")


def import_policy_from_csv(file_path: str) -> Dict:
    """Import a policy configuration from CSV format.
    
    Args:
        file_path: Path to CSV file to import
    
    Returns:
        Dict with 'general', 'revenues', 'outs' keys
    
    Raises:
        IOError: If file reading fails
        ValueError: If CSV format is invalid
    """
    logger.info(f"Importing policy from CSV: {file_path}")
    
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Policy file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # Split by section headers
        sections = {}
        current_section = None
        section_lines = []

        for line in content.split('\n'):
            line_stripped = line.strip()
            if line_stripped.startswith('[') and line_stripped.endswith(']'):
                if current_section and section_lines:
                    sections[current_section] = '\n'.join([l for l in section_lines if l.strip()])
                current_section = line_stripped.strip('[]')
                section_lines = []
            elif current_section and line.strip():
                section_lines.append(line)

        if current_section and section_lines:
            sections[current_section] = '\n'.join([l for l in section_lines if l.strip()])

        result = {}

        # Parse General Parameters
        if 'General Parameters' not in sections:
            raise ValueError("Missing 'General Parameters' section in CSV")

        general_df = pd.read_csv(io.StringIO(sections['General Parameters']))
        result['general'] = dict(zip(general_df['Parameter'], general_df['Value']))
        logger.debug(f"Imported {len(result['general'])} general parameters")

        # Parse Revenues
        result['revenues'] = []
        if 'Revenues' in sections and sections['Revenues'].strip():
            revenues_df = pd.read_csv(io.StringIO(sections['Revenues']))
            result['revenues'] = revenues_df.to_dict('records')
            logger.debug(f"Imported {len(result['revenues'])} revenue sources")

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
                i = 1
                while f'alloc_{i}_source' in row:
                    source = row[f'alloc_{i}_source']
                    percent = row.get(f'alloc_{i}_percent', 0)
                    if pd.notna(source) and source:
                        out['allocations'].append({'source': source, 'percent': percent})
                    i += 1
                result['outs'].append(out)
            logger.debug(f"Imported {len(result['outs'])} spending categories")

        logger.info(f"✓ Policy imported successfully from {file_path}")
        return result
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise IOError(f"Policy file not found: {file_path}")
    except (pd.errors.ParserError, ValueError) as e:
        logger.error(f"Invalid CSV format: {e}")
        raise IOError(f"Invalid CSV format in policy file: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while importing policy: {e}")
        raise IOError(f"Failed to import policy: {str(e)}")


def export_results_to_file(
    current_df: Optional[pd.DataFrame],
    proposed_df: Optional[pd.DataFrame],
    summary_table: Optional[pd.DataFrame],
    file_path: str,
    diff_table: Optional[pd.DataFrame] = None,
    normalized_table: Optional[pd.DataFrame] = None,
) -> None:
    """Export simulation results to file (Excel or CSV).

    Args:
        current_df: DataFrame with current policy results
        proposed_df: DataFrame with proposed policy results
        summary_table: DataFrame with CBO summary metrics
        file_path: Path to save results
        diff_table: Optional DataFrame with differences vs baseline
        normalized_table: Optional DataFrame with normalized metrics
    
    Raises:
        IOError: If file writing fails
    """
    logger.info(f"Exporting results to: {file_path}")
    
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        if file_path.endswith('.xlsx'):
            with pd.ExcelWriter(file_path, engine='openpyxl') as writer:
                if current_df is not None and not current_df.empty:
                    current_df.to_excel(writer, sheet_name='Current Policy', index=False)
                    logger.debug(f"Wrote {len(current_df)} rows to 'Current Policy' sheet")
                
                if proposed_df is not None and not proposed_df.empty:
                    proposed_df.to_excel(writer, sheet_name='Proposed Policy', index=False)
                    logger.debug(f"Wrote {len(proposed_df)} rows to 'Proposed Policy' sheet")
                
                if summary_table is not None and not summary_table.empty:
                    summary_table.to_excel(writer, sheet_name='CBO Summary', index=False)
                    logger.debug(f"Wrote summary table to 'CBO Summary' sheet")
                
                if diff_table is not None and not diff_table.empty:
                    diff_table.to_excel(writer, sheet_name='Diff vs Baseline', index=False)
                    logger.debug(f"Wrote {len(diff_table)} rows to 'Diff vs Baseline' sheet")
                
                if normalized_table is not None and not normalized_table.empty:
                    normalized_table.to_excel(writer, sheet_name='Normalized', index=False)
                    logger.debug(f"Wrote {len(normalized_table)} rows to 'Normalized' sheet")
        else:
            # CSV format
            with open(file_path, 'w', newline='', encoding='utf-8') as f:
                if summary_table is not None and not summary_table.empty:
                    f.write('CBO-Style Summary\n')
                    summary_table.to_csv(f, index=False)
                    f.write('\n')
                    logger.debug("Wrote CBO summary section")

                f.write('Simulation Results\n')
                combined = pd.concat([
                    (current_df.assign(Policy='Current') if current_df is not None and not current_df.empty else pd.DataFrame()),
                    (proposed_df.assign(Policy='Proposed') if proposed_df is not None and not proposed_df.empty else pd.DataFrame())
                ], ignore_index=True)
                combined.to_csv(f, index=False)
                logger.debug(f"Wrote {len(combined)} rows of combined results")

                if diff_table is not None and not diff_table.empty:
                    f.write('\nDiff vs Baseline\n')
                    diff_table.to_csv(f, index=False)
                    logger.debug(f"Wrote {len(diff_table)} rows of diffs")

                if normalized_table is not None and not normalized_table.empty:
                    f.write('\nNormalized Per Capita\n')
                    normalized_table.to_csv(f, index=False)
                    logger.debug(f"Wrote {len(normalized_table)} rows of normalized metrics")
        
        logger.info(f"✓ Results exported successfully to {file_path}")
        
    except IOError as e:
        logger.error(f"File I/O error while exporting results: {e}")
        raise IOError(f"Failed to export results: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while exporting results: {e}")
        raise IOError(f"Failed to export results: {str(e)}")


def load_json(file_path: str) -> Dict[str, Any]:
    """Load JSON configuration file.
    
    Args:
        file_path: Path to JSON file
    
    Returns:
        Parsed JSON as dictionary
    
    Raises:
        IOError: If file reading fails
        ValueError: If JSON is invalid
    """
    logger.info(f"Loading JSON from: {file_path}")
    
    try:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        logger.debug(f"Loaded JSON with {len(data)} top-level keys")
        return data
        
    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        raise IOError(f"File not found: {file_path}")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON: {e}")
        raise ValueError(f"Invalid JSON in {file_path}: {str(e)}")
    except Exception as e:
        logger.error(f"Error loading JSON: {e}")
        raise IOError(f"Failed to load JSON: {str(e)}")


def save_json(data: Dict[str, Any], file_path: str, pretty: bool = True) -> None:
    """Save data as JSON file.
    
    Args:
        data: Dictionary to save
        file_path: Path to write JSON file
        pretty: If True, pretty-print JSON (default: True)
    
    Raises:
        IOError: If file writing fails
    """
    logger.info(f"Saving JSON to: {file_path}")
    
    try:
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(
                data,
                f,
                indent=2 if pretty else None,
                ensure_ascii=False
            )
        
        logger.debug(f"Saved JSON with {len(data)} top-level keys")
        logger.info(f"✓ JSON saved successfully to {file_path}")
        
    except IOError as e:
        logger.error(f"File I/O error while saving JSON: {e}")
        raise IOError(f"Failed to save JSON: {str(e)}")
    except Exception as e:
        logger.error(f"Unexpected error while saving JSON: {e}")
        raise IOError(f"Failed to save JSON: {str(e)}")

