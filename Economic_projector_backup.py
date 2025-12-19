import tkinter as tk
from tkinter import ttk, scrolledtext, filedialog, messagebox, simpledialog
import os
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from copy import deepcopy

from defaults import initial_revenues, initial_outs, initial_general
from core import simulate_years, calculate_cbo_summary
from ui import ScrollableFrame
from utils import export_policy_to_csv, import_policy_from_csv, export_results_to_file


# ============================================================================
# EconomicProjectorApp - Main Application Class
# ============================================================================


class EconomicProjectorApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Economic Policy Simulator - Comparative Analysis")

        # Store both current and proposed policy data
        self.current_policy = {
            'revenues': deepcopy(initial_revenues),
            'outs': deepcopy(initial_outs),
            'general': deepcopy(initial_general),
        }

        # Initialize lists for proposed policy
        self.revenue_list = []
        self.out_list = []
        self.all_alloc_combos = []

        # Initialize lists for current policy
        self.current_revenue_list = []
        self.current_out_list = []

        # Store latest baseline simulation results
        self.current_simulation_results = None

        # Scenario / location state (foundation for multi-country comparison)
        self.current_location = {
            'country': 'United States',
            'region': None,
            'subregion': None,
        }

        # Scenario management and wizard progression flags
        self.active_scenario_name = "Scenario 1"
        self.scenarios = {}  # name -> scenario dict (location, policies, results)
        self.scenario_confirmed = False
        self.baseline_run = False
        self.proposed_run = False

        # Main notebook: Scenario, Current, Proposed, Comparison
        self.notebook = ttk.Notebook(self.root)
    def __init__(self, root):
        self.root = root
        self.root.title("Economic Policy Simulator - Comparative Analysis")

        # Store both current and proposed policy data
        self.current_policy = {
            'revenues': deepcopy(initial_revenues),
            'outs': deepcopy(initial_outs),
            'general': deepcopy(initial_general),
        }

        # Initialize lists for proposed policy
        self.revenue_list = []
        self.out_list = []
        self.all_alloc_combos = []

        # Initialize lists for current policy
        self.current_revenue_list = []
        self.current_out_list = []

        # Store latest baseline simulation results
        self.current_simulation_results = None

        # Scenario / location state (foundation for multi-country comparison)
        self.current_location = {
            'country': 'United States',
            'region': None,
            'subregion': None,
        }

        # Scenario management and wizard progression flags
        self.active_scenario_name = "Scenario 1"
        self.scenarios = {}  # name -> scenario dict (location, policies, results)
        self.scenario_confirmed = False
        self.baseline_run = False
        self.proposed_run = False

        # Main notebook: Scenario, Current, Proposed, Comparison
        self.notebook = ttk.Notebook(self.root)
        self.notebook.grid(row=0, column=0, sticky="nsew", padx=10, pady=10)

        # Scenario Setup / Location tab (wizard entry point)
        self.scenario_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.scenario_tab, text="Scenario Setup")

        # Current policy tab - now with sub-notebook structure like Proposed
        self.current_parent = ttk.Frame(self.notebook)
        self.notebook.add(self.current_parent, text="Current Policy")
        self.current_tab_index = self.notebook.index(self.current_parent)

        self.current_notebook = ttk.Notebook(self.current_parent)
        self.current_notebook.grid(row=0, column=0, sticky="nsew")
        self.current_parent.columnconfigure(0, weight=1)
        self.current_parent.rowconfigure(0, weight=1)

        self.current_general_tab = ttk.Frame(self.current_notebook)
        self.current_notebook.add(self.current_general_tab, text="General")

        self.current_revenues_tab = ttk.Frame(self.current_notebook)
        self.current_notebook.add(self.current_revenues_tab, text="Revenues")

        self.current_outs_tab = ttk.Frame(self.current_notebook)
        self.current_notebook.add(self.current_outs_tab, text="Out Categories")

        # Proposed policy tab contains its own sub-notebook for General/Revenues/Outs
        self.proposed_parent = ttk.Frame(self.notebook)
        self.notebook.add(self.proposed_parent, text="Proposed Policy")
        self.proposed_tab_index = self.notebook.index(self.proposed_parent)

        self.proposed_notebook = ttk.Notebook(self.proposed_parent)
        self.proposed_notebook.grid(row=0, column=0, sticky="nsew")
        # Allow the proposed parent to expand so its child tabs can fill width
        self.proposed_parent.columnconfigure(0, weight=1)
        self.proposed_parent.rowconfigure(0, weight=1)

        self.general_tab = ttk.Frame(self.proposed_notebook)
        self.proposed_notebook.add(self.general_tab, text="General")

        self.revenues_tab = ttk.Frame(self.proposed_notebook)
        self.proposed_notebook.add(self.revenues_tab, text="Revenues")

        self.outs_tab = ttk.Frame(self.proposed_notebook)
        self.proposed_notebook.add(self.outs_tab, text="Out Categories")

        # Comparison / Output tab
        self.output_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.output_tab, text="Comparison")
        self.comparison_tab_index = self.notebook.index(self.output_tab)

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.notebook.columnconfigure(0, weight=1)
        self.notebook.rowconfigure(0, weight=1)

        # Build proposed policy UI (editable)
        self.setup_general_tab()
        self.setup_revenues_tab()
        self.setup_outs_tab()

        # Build comparison/output UI
        self.setup_output_tab()

        # Load initial data into proposed UI (start as a copy of current policy)
        for rev in deepcopy(self.current_policy['revenues']):
            self.add_revenue(initial=rev)

        for out in deepcopy(self.current_policy['outs']):
            self.add_out(initial=out)

        # Populate the Current Policy read-only tab
        # Make the Current Policy tab mirror the Proposed tab (editable controls populated with current values)
        # This ensures the Current tab is structurally identical to Proposed but bound to current values.
        self.edit_current_policy()

        # Build scenario setup / location UI (wizard step 1)
        self.setup_scenario_tab()

        # Wizard gating: start with only Scenario tab enabled
        try:
            scenario_index = self.notebook.index(self.scenario_tab)
            self.current_tab_index = self.notebook.index(self.current_parent)
            self.proposed_tab_index = self.notebook.index(self.proposed_parent)
            self.comparison_tab_index = self.notebook.index(self.output_tab)

            self.notebook.tab(self.current_tab_index, state="disabled")
            self.notebook.tab(self.proposed_tab_index, state="disabled")
            self.notebook.tab(self.comparison_tab_index, state="disabled")
        except Exception:
            # If anything goes wrong, fail open so the app still works
            pass

    def setup_scenario_tab(self):
        """Create the Scenario Setup / Location wizard tab.

        Phase 1 goal: simple country/state selectors and a button
        to continue into the Current Policy tab. This is the
        foundation for later multi-country comparisons and
        policy catalog loading.
        """
        self.scenario_tab.columnconfigure(0, weight=1)
        self.scenario_tab.rowconfigure(0, weight=0)
        self.scenario_tab.rowconfigure(1, weight=1)

        header = ttk.Label(
            self.scenario_tab,
            text=(
                "Scenario Setup / Location\n\n"
                "Select the geographic focus for this analysis. "
                "Later, this will drive which baseline policies "
                "and data sources are used."
            ),
            justify="left",
        )
        header.grid(row=0, column=0, sticky="w", padx=10, pady=(10, 5))

        form = ttk.Frame(self.scenario_tab)
        form.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        form.columnconfigure(1, weight=1)

        # Scenario name
        ttk.Label(form, text="Scenario name:").grid(row=0, column=0, sticky="w", padx=(0, 5), pady=5)
        self.scenario_name_var = tk.StringVar(value=self.active_scenario_name)
        self.scenario_name_entry = ttk.Entry(form, textvariable=self.scenario_name_var)
        self.scenario_name_entry.grid(row=0, column=1, sticky="ew", pady=5)

        # Country selector
        ttk.Label(form, text="Country:").grid(row=1, column=0, sticky="w", padx=(0, 5), pady=5)
        self.country_var = tk.StringVar(value=self.current_location.get("country", "United States"))
        self.country_combo = ttk.Combobox(
            form,
            textvariable=self.country_var,
            state="readonly",
            values=[
                "United States",
                "Canada",
                "United Kingdom",
                "Germany",
                "France",
                "Japan",
                "Australia",
            ],
        )
        self.country_combo.grid(row=1, column=1, sticky="ew", pady=5)
        self.country_combo.bind("<<ComboboxSelected>>", self.on_country_selected)

        # Region/state selector (optional)
        ttk.Label(form, text="State / Region (optional):").grid(
            row=2,
            column=0,
            sticky="w",
            padx=(0, 5),
            pady=5,
        )
        self.region_var = tk.StringVar(value=self.current_location.get("region") or "")
        self.region_entry = ttk.Entry(form, textvariable=self.region_var)
        self.region_entry.grid(row=2, column=1, sticky="ew", pady=5)

        # Subregion selector (city/county)
        ttk.Label(form, text="City / County (optional):").grid(
            row=3,
            column=0,
            sticky="w",
            padx=(0, 5),
            pady=5,
        )
        self.subregion_var = tk.StringVar(value=self.current_location.get("subregion") or "")
        self.subregion_entry = ttk.Entry(form, textvariable=self.subregion_var)
        self.subregion_entry.grid(row=3, column=1, sticky="ew", pady=5)

        # Buttons: save scenario + continue
        buttons_frame = ttk.Frame(form)
        buttons_frame.grid(row=4, column=0, columnspan=2, sticky="ew", pady=(10, 5))
        buttons_frame.columnconfigure(0, weight=0)
        buttons_frame.columnconfigure(1, weight=0)
        buttons_frame.columnconfigure(2, weight=1)

        save_btn = ttk.Button(
            buttons_frame,
            text="Save Scenario",
            command=self.save_current_as_scenario,
        )
        save_btn.grid(row=0, column=0, padx=(0, 5))

        continue_btn = ttk.Button(
            buttons_frame,
            text="Continue to Current Policy",
            command=self.confirm_scenario_and_go_to_current,
        )
        continue_btn.grid(row=0, column=1, padx=(0, 5))

        note = ttk.Label(
            form,
            text=(
                "Tip: Define a scenario name, pick a location, then save it. "
                "You can later compare any two saved scenarios (including "
                "different regions within the same country)."
            ),
            wraplength=500,
            justify="left",
        )
        note.grid(row=5, column=0, columnspan=2, sticky="w", pady=(10, 0))


        # Simple listbox to show saved scenarios
        list_frame = ttk.LabelFrame(self.scenario_tab, text="Saved scenarios (for comparison)")
        list_frame.grid(row=2, column=0, sticky="nsew", padx=10, pady=(0, 10))
        list_frame.columnconfigure(0, weight=1)
        list_frame.rowconfigure(0, weight=1)

        self.scenario_listbox = tk.Listbox(list_frame, height=4)
        self.scenario_listbox.grid(row=0, column=0, sticky="nsew")
        self.refresh_scenario_listbox()

    def on_country_selected(self, event=None):
        """Placeholder hook for when a country is chosen.

        In later phases this will trigger loading of country-specific
        default policies and region lists. For now we simply keep
        the selection in current_location.
        """
        self.current_location["country"] = self.country_var.get()

    def confirm_scenario_and_go_to_current(self):
        """Persist location selection and switch to the Current Policy tab.

        This is step 1 of the wizard: once a location is set, the
        user refines the baseline on the Current Policy tab, then
        proceeds to the Proposed Policy and Comparison tabs.
        """
        self.current_location["country"] = self.country_var.get() or "United States"
        self.current_location["region"] = self.region_var.get().strip() or None

        # Also refresh scenarios whenever the tab is (re)opened
        self.refresh_scenario_listbox()

    def refresh_scenario_listbox(self):
        """Refresh the list of saved scenarios in the Scenario tab."""
        if not hasattr(self, "scenario_listbox"):
            return
        self.scenario_listbox.delete(0, tk.END)
        for name, data in self.scenarios.items():
            loc = data.get("location", {})
            country = loc.get("country") or "?"
            region = loc.get("region") or ""
            sub = loc.get("subregion") or ""
            label_parts = [country]
            if region:
                label_parts.append(region)
            if sub:
                label_parts.append(sub)
            display = f"{name}  —  " + " / ".join(label_parts)
            self.scenario_listbox.insert(tk.END, display)

    def save_current_as_scenario(self):
        """Capture current location + baseline/proposed configs as a named scenario."""
        name = (self.scenario_name_var.get() or "Scenario").strip()
        if not name:
            name = "Scenario"
        # Ensure a simple unique name if already present
        base = name
        i = 2
        while name in self.scenarios:
            name = f"{base} ({i})"
            i += 1

        # Snapshot location
        location = {
            "country": self.current_location.get("country"),
            "region": self.current_location.get("region"),
            "subregion": self.current_location.get("subregion"),
        }

        # Snapshot current policy config (baseline)
        try:
            current_values = self.collect_current_values()
        except Exception:
            current_values = deepcopy(self.current_policy)

        # Snapshot proposed policy config from the editor
        proposed_general = {}
        for key, entry in self.general_entries.items():
            if key == "surplus_redirect_target":
                proposed_general[key] = entry.get()
            else:
                try:
                    proposed_general[key] = float(entry.get() or 0)
                except Exception:
                    proposed_general[key] = 0.0

        proposed_revenues = []
        for d in self.revenue_list:
            try:
                proposed_revenues.append({
                    "name": d["name_entry"].get(),
                    "is_percent": d["type_var"].get() == "%",
                    "value": float(d["value_entry"].get() or 0),
                    "desc": d["desc_entry"].get(),
                    "alloc_health": float(d["alloc_health_entry"].get() or 0),
                    "alloc_states": float(d["alloc_states_entry"].get() or 0),
                    "alloc_federal": float(d["alloc_federal_entry"].get() or 0),
                })
            except Exception:
                continue

        proposed_outs = []
        for d in self.out_list:
            try:
                allocations = []
                for a in d["alloc_list"]:
                    allocations.append({
                        "source": a["combo"].get(),
                        "percent": float(a["percent_entry"].get() or 0),
                    })
                proposed_outs.append({
                    "name": d["name_entry"].get(),
                    "is_percent": d["type_var"].get() == "%",
                    "value": float(d["value_entry"].get() or 0),
                    "allocations": allocations,
                })
            except Exception:
                continue

        self.scenarios[name] = {
            "location": location,
            "baseline": deepcopy(current_values),
            "proposed": {
                "general": proposed_general,
                "revenues": proposed_revenues,
                "outs": proposed_outs,
            },
            "results": {
                "baseline": deepcopy(self.current_simulation_results),
                # proposed results will be filled after run_simulation
            },
        }
        self.active_scenario_name = name
        self.refresh_scenario_listbox()
        try:
            if hasattr(self, "current_tab_index"):
                self.notebook.tab(self.current_tab_index, state="normal")
            # Keep Proposed and Comparison gated for now
            if hasattr(self, "proposed_tab_index"):
                self.notebook.tab(self.proposed_tab_index, state="disabled")
            if hasattr(self, "comparison_tab_index"):
                self.notebook.tab(self.comparison_tab_index, state="disabled")
        except Exception:
            pass

        # Switch notebook to the Current Policy tab
        try:
            target_index = self.current_tab_index
        except Exception:
            target_index = 1
        self.notebook.select(target_index)

        # Update scenario banner if it already exists
        try:
            self.update_scenario_banner()
        except Exception:
            pass

    def update_scenario_banner(self):
        """Update the scenario summary label on the Comparison tab, if present."""
        try:
            pieces = []
            country = self.current_location.get("country")
            region = self.current_location.get("region")
            subregion = self.current_location.get("subregion")
            if country:
                pieces.append(country)
            if region:
                pieces.append(region)
            if subregion:
                pieces.append(subregion)
            if pieces:
                text = "Scenario: " + " / ".join(pieces)
            else:
                text = "Scenario: (no scenario set)"
            if hasattr(self, "scenario_label"):
                self.scenario_label.configure(text=text)
        except Exception:
            # Fail silently; banner is purely cosmetic
            pass


        try:
            self.update_scenario_banner()
        except Exception:
            pass

    def setup_general_tab(self):
        # Configure grid weights for proper expansion
        self.general_tab.columnconfigure(0, weight=1)
        self.general_tab.rowconfigure(1, weight=1)  # Make param_frame expandable

        # Controls at top
        ctrl_frame = ttk.Frame(self.general_tab)
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=3)

        # Left side - simulation controls
        sim_frame = ttk.LabelFrame(ctrl_frame, text="Simulation Controls")
        sim_frame.grid(row=0, column=0, padx=5, sticky="w")

        run_button = ttk.Button(sim_frame, text="Run Simulation", command=self.run_simulation)
        run_button.grid(row=0, column=0, padx=2)

        preview_button = ttk.Button(sim_frame, text="Preview Flow", command=lambda: self.show_flow_preview(use_current=False))
        preview_button.grid(row=0, column=1, padx=2)

        # Right side - import/export controls
        io_frame = ttk.LabelFrame(ctrl_frame, text="Import/Export")
        io_frame.grid(row=0, column=1, padx=5, sticky="e")

        import_btn = ttk.Button(io_frame, text="Import from CSV", command=self.import_proposed_from_csv)
        import_btn.grid(row=0, column=0, padx=2)

        export_btn = ttk.Button(io_frame, text="Export to CSV", command=self.export_proposed_to_csv)
        export_btn.grid(row=0, column=1, padx=2)

        ctrl_frame.columnconfigure(1, weight=1)  # Push io_frame to the right

        # Scrollable parameter frame for better space utilization
        param_frame = ttk.LabelFrame(self.general_tab, text="Economic Parameters")
        param_frame.grid(row=1, column=0, padx=5, pady=5, sticky="nsew")

        param_frame.columnconfigure(0, weight=1)
        param_frame.rowconfigure(0, weight=1)

        # Use ScrollableFrame for parameters
        scroll_container = ScrollableFrame(param_frame)
        scroll_container.grid(row=0, column=0, sticky="nsew")

        # Parameter entries with tooltips
        self.general_entries = {}
        row = 0
        tooltips = {
            'gdp': "Current Gross Domestic Product in trillion $",
            'gdp_growth_rate': "Annual GDP growth rate projection (can be negative for recession)",
            'inflation_rate': "Expected annual inflation rate (warning if >50%)",
            'national_debt': "Current national debt in trillion $",
            'interest_rate': "Average interest rate on national debt",
            'surplus_redirect_post_debt': "Percentage of surplus redirected after debt clearance",
            'surplus_redirect_target': "Which expenditure category receives surplus after debt is cleared",
            'transition_fund': "Emergency/transition fund allocation",
            'simulation_years': "Number of years to simulate",
            'stop_on_debt_explosion': "1=stop simulation if debt/GDP > 1000%, 0=continue with warning",
            'debt_drag_factor': "GDP growth reduction per 10% debt/GDP increase (e.g., 0.1 = -0.1% per 10% debt/GDP). Based on CBO/IMF fiscal drag models."
        }

        for key, value in initial_general.items():
            # Skip surplus_redirect_target if it's a string (handle separately)
            if key == 'surplus_redirect_target':
                continue

            unit = " (%)" if 'rate' in key or 'redirect' in key else " (trillions $)" if key in ['gdp', 'national_debt', 'transition_fund'] else ""
            container = ttk.Frame(scroll_container.scrollable_frame)
            container.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
            container.columnconfigure(1, weight=1)

            label = ttk.Label(container, text=key.replace('_', ' ').title() + unit + ":")
            label.grid(row=0, column=0, sticky="w", padx=(0, 10))

            entry = ttk.Entry(container)
            entry.insert(0, str(value))
            entry.grid(row=0, column=1, sticky="ew")

            # Add tooltip
            tooltip = tooltips.get(key, "")
            if tooltip:
                self.create_tooltip(label, tooltip)

            self.general_entries[key] = entry
            row += 1

        # Add surplus_redirect_target as a dropdown (string value)
        if 'surplus_redirect_target' in initial_general:
            container = ttk.Frame(scroll_container.scrollable_frame)
            container.grid(row=row, column=0, sticky="ew", padx=5, pady=2)
            container.columnconfigure(1, weight=1)

            label = ttk.Label(container, text="Surplus Redirect Target:")
            label.grid(row=0, column=0, sticky="w", padx=(0, 10))

            # P0 FIX: Dynamically populate from out category names instead of hardcoded values
            # Start with initial out names, will update when outs change
            initial_out_names = [out['name'] for out in initial_outs]
            redirect_combo = ttk.Combobox(container, values=initial_out_names)
            redirect_combo.set(initial_general['surplus_redirect_target'])
            redirect_combo.grid(row=0, column=1, sticky="ew")

            tooltip = tooltips.get('surplus_redirect_target', "")
            if tooltip:
                self.create_tooltip(label, tooltip)

            self.general_entries['surplus_redirect_target'] = redirect_combo
            # Store reference for dynamic updates
            self.surplus_redirect_combo = redirect_combo
            row += 1

    def setup_revenues_tab(self):
        add_button = ttk.Button(self.revenues_tab, text="Add Revenue", command=self.add_revenue)
        add_button.grid(row=0, column=0, columnspan=9, pady=5)

        # Make the revenues tab expand to fill available horizontal space
        self.revenues_tab.columnconfigure(0, weight=1)
        self.revenues_tab.rowconfigure(1, weight=1)

        # Scrollable container for many revenue rows
        self.revenues_container = ScrollableFrame(self.revenues_tab)
        self.revenues_container.grid(row=1, column=0, sticky='nsew')

        # Configure columns with specific weights for proper alignment
        self.revenues_container.scrollable_frame.columnconfigure(0, weight=2, minsize=120)  # Name
        self.revenues_container.scrollable_frame.columnconfigure(1, weight=0, minsize=30)   # $ radio
        self.revenues_container.scrollable_frame.columnconfigure(2, weight=0, minsize=30)   # % radio
        self.revenues_container.scrollable_frame.columnconfigure(3, weight=0, minsize=80)   # Value
        self.revenues_container.scrollable_frame.columnconfigure(4, weight=3, minsize=150)  # Description
        self.revenues_container.scrollable_frame.columnconfigure(5, weight=0, minsize=100)  # Alloc Health
        self.revenues_container.scrollable_frame.columnconfigure(6, weight=0, minsize=100)  # Alloc States
        self.revenues_container.scrollable_frame.columnconfigure(7, weight=0, minsize=100)  # Alloc Federal
        self.revenues_container.scrollable_frame.columnconfigure(8, weight=0, minsize=60)   # Delete

        # Add header row inside the scrollable frame
        header_parent = self.revenues_container.scrollable_frame
        ttk.Label(header_parent, text="Name", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Type", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=1, columnspan=2, sticky='ew', pady=2)
        ttk.Label(header_parent, text="Value", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=3, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Description", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=4, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Alloc Health (%)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=5, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Alloc States (%)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=6, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Alloc Federal (%)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=7, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Actions", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=8, sticky='ew', padx=2, pady=2)

        # Ensure the outer frame expands when the window resizes
        self.revenues_tab.update_idletasks()

    def add_revenue(self, initial=None):
        row = len(self.revenue_list)
        parent = self.revenues_container.scrollable_frame

        # Account for header row at row 0, data starts at row 1
        grid_row = 1 + row * 2

        # Insert a separator above each row for clarity
        sep = ttk.Separator(parent, orient='horizontal')
        sep.grid(row=grid_row, column=0, columnspan=9, sticky='ew', pady=3)

        name_entry = ttk.Entry(parent)
        name_entry.grid(row=grid_row+1, column=0, sticky='ew', padx=2)

        # Use explicit string values for type to simplify checks later
        type_var = tk.StringVar(value='$')
        radio_dollar = ttk.Radiobutton(parent, text='$', variable=type_var, value='$')
        radio_dollar.grid(row=grid_row+1, column=1)
        radio_percent = ttk.Radiobutton(parent, text='%', variable=type_var, value='%')
        radio_percent.grid(row=grid_row+1, column=2)

        value_entry = ttk.Entry(parent)
        value_entry.grid(row=grid_row+1, column=3, padx=2)

        desc_entry = ttk.Entry(parent)
        desc_entry.grid(row=grid_row+1, column=4, sticky="ew", padx=2)

        alloc_health_entry = tk.Spinbox(parent, from_=0, to=100, increment=0.1, format="%.1f")
        alloc_health_entry.grid(row=grid_row+1, column=5, padx=2)

        alloc_states_entry = tk.Spinbox(parent, from_=0, to=100, increment=0.1, format="%.1f")
        alloc_states_entry.grid(row=grid_row+1, column=6, padx=2)

        alloc_federal_entry = tk.Spinbox(parent, from_=0, to=100, increment=0.1, format="%.1f")
        alloc_federal_entry.grid(row=grid_row+1, column=7, padx=2)

        delete_button = ttk.Button(parent, text='Delete', command=lambda r=row: self.delete_revenue(r))
        delete_button.grid(row=grid_row+1, column=8, padx=2)

        d = {'name_entry': name_entry, 'type_var': type_var, 'value_entry': value_entry, 'desc_entry': desc_entry,
             'alloc_health_entry': alloc_health_entry, 'alloc_states_entry': alloc_states_entry, 'alloc_federal_entry': alloc_federal_entry,
             'radio_dollar': radio_dollar, 'radio_percent': radio_percent,
             'delete_button': delete_button, 'row': row}

        # Keep reference to separator so it can be removed later
        d['sep'] = sep

        self.revenue_list.append(d)

        if initial:
            name_entry.insert(0, initial['name'])
            type_var.set('%' if initial.get('is_percent') else '$')
            value_entry.insert(0, str(initial['value']))
            desc_entry.insert(0, initial['desc'])
            alloc_health_entry.delete(0, 'end')
            alloc_health_entry.insert(0, str(initial.get('alloc_health',0)))
            alloc_states_entry.delete(0, 'end')
            alloc_states_entry.insert(0, str(initial.get('alloc_states',0)))
            alloc_federal_entry.delete(0, 'end')
            alloc_federal_entry.insert(0, str(initial.get('alloc_federal',0)))

    def delete_revenue(self, row):
        for d in self.revenue_list:
            if d['row'] == row:
                for widget in [d['name_entry'], d['radio_dollar'], d['radio_percent'], d['value_entry'], d['desc_entry'], d['alloc_health_entry'], d['alloc_states_entry'], d['alloc_federal_entry'], d['delete_button']]:
                    try:
                        widget.destroy()
                    except Exception:
                        pass
                try:
                    d['sep'].destroy()
                except Exception:
                    pass
                self.revenue_list.remove(d)
                break

        # Regrid remaining
        for i, d in enumerate(self.revenue_list):
            new_row = i + 2
            d['name_entry'].grid(row=new_row)
            d['radio_dollar'].grid(row=new_row)
            d['radio_percent'].grid(row=new_row)
            d['value_entry'].grid(row=new_row)
            d['desc_entry'].grid(row=new_row)
            d['alloc_health_entry'].grid(row=new_row)
            d['alloc_states_entry'].grid(row=new_row)
            d['alloc_federal_entry'].grid(row=new_row)
            d['delete_button'].grid(row=new_row)
            d['row'] = new_row

    def update_surplus_redirect_combo(self):
        """
        P0 FIX: Update surplus redirect target combobox with current out category names.
        Called whenever outs are added/deleted to keep dropdown in sync.
        """
        if hasattr(self, 'surplus_redirect_combo'):
            out_names = [d['name_entry'].get() for d in self.out_list if d['name_entry'].get().strip()]
            if not out_names:
                out_names = ['healthcare_social', 'states', 'federal']  # Fallback
            self.surplus_redirect_combo['values'] = out_names

    # Similar for outs_tab

    def setup_outs_tab(self):
        add_button = ttk.Button(self.outs_tab, text="Add Out Category", command=self.add_out)
        add_button.grid(row=0, column=0, columnspan=9, pady=5)

        # Allow the outs tab to expand horizontally
        self.outs_tab.columnconfigure(0, weight=1)
        self.outs_tab.rowconfigure(1, weight=1)

        # Scrollable container for out rows
        self.outs_container = ScrollableFrame(self.outs_tab)
        self.outs_container.grid(row=1, column=0, sticky='nsew')

        # Configure columns with specific weights for proper alignment
        self.outs_container.scrollable_frame.columnconfigure(0, weight=2, minsize=120)  # Name
        self.outs_container.scrollable_frame.columnconfigure(1, weight=0, minsize=30)   # $ radio
        self.outs_container.scrollable_frame.columnconfigure(2, weight=0, minsize=30)   # % radio
        self.outs_container.scrollable_frame.columnconfigure(3, weight=0, minsize=100)  # Value
        self.outs_container.scrollable_frame.columnconfigure(4, weight=3, minsize=200)  # Allocations
        self.outs_container.scrollable_frame.columnconfigure(5, weight=0, minsize=100)  # Add Alloc button
        self.outs_container.scrollable_frame.columnconfigure(6, weight=0, minsize=60)   # Delete

        # Scenario comparison selectors
        compare_frame = ttk.LabelFrame(self.output_tab, text="Compare saved scenarios")
        compare_frame.grid(row=1, column=1, sticky="ne", padx=5, pady=5)

        ttk.Label(compare_frame, text="Left scenario:").grid(row=0, column=0, sticky="w")
        self.compare_left_var = tk.StringVar()
        self.compare_left_combo = ttk.Combobox(compare_frame, textvariable=self.compare_left_var, state="readonly")
        self.compare_left_combo.grid(row=0, column=1, sticky="ew", padx=(5, 0))

        ttk.Label(compare_frame, text="Right scenario:").grid(row=1, column=0, sticky="w")
        self.compare_right_var = tk.StringVar()
        self.compare_right_combo = ttk.Combobox(compare_frame, textvariable=self.compare_right_var, state="readonly")
        self.compare_right_combo.grid(row=1, column=1, sticky="ew", padx=(5, 0))

        compare_frame.columnconfigure(1, weight=1)

        self.refresh_comparison_scenario_combos()


        # Add header row inside the scrollable frame
        header_parent = self.outs_container.scrollable_frame
        ttk.Label(header_parent, text="Name", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Type", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=1, columnspan=2, sticky='ew', pady=2)
        ttk.Label(header_parent, text="Value (target)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=3, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Allocations (add below)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=4, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Actions", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=5, columnspan=2, sticky='ew', padx=2, pady=2)

        # Give immediate layout a chance to settle for proper sizing
        self.outs_tab.update_idletasks()

    def add_out(self, initial=None):
        row = len(self.out_list)
        parent = self.outs_container.scrollable_frame

        # Account for header row at row 0, data starts at row 1
        grid_row = 1 + row * 2

        # separator
        sep = ttk.Separator(parent, orient='horizontal')
        sep.grid(row=grid_row, column=0, columnspan=7, sticky='ew', pady=3)

        name_entry = ttk.Entry(parent)
        name_entry.grid(row=grid_row+1, column=0, sticky='ew', padx=2)

        # Use string values for consistency with revenues
        type_var = tk.StringVar(value='$')
        radio_dollar = ttk.Radiobutton(parent, text='$', variable=type_var, value='$')
        radio_dollar.grid(row=grid_row+1, column=1)
        radio_percent = ttk.Radiobutton(parent, text='%', variable=type_var, value='%')
        radio_percent.grid(row=grid_row+1, column=2)

        value_entry = ttk.Entry(parent)
        value_entry.grid(row=grid_row+1, column=3, padx=2)

        alloc_parent = ttk.Frame(parent)
        alloc_parent.grid(row=grid_row+1, column=4, rowspan=1, sticky="nsew", padx=2)

        # Create placeholder button - will update command after d is created
        add_alloc_button = ttk.Button(parent, text='Add Allocation')
        add_alloc_button.grid(row=grid_row+1, column=5, padx=2)

        delete_button = ttk.Button(parent, text='Delete', command=lambda r=row: self.delete_out(r))
        delete_button.grid(row=grid_row+1, column=6, padx=2)

        d = {'name_entry': name_entry, 'type_var': type_var, 'value_entry': value_entry, 'alloc_parent': alloc_parent, 'add_alloc_button': add_alloc_button, 'delete_button': delete_button, 'row': row, 'alloc_list': [], 'radio_dollar': radio_dollar, 'radio_percent': radio_percent}
        d['sep'] = sep

        # Now configure the button command with the correct d reference
        add_alloc_button.config(command=lambda p=alloc_parent, out_d=d: self.add_allocation(p, out_d))

        self.out_list.append(d)

        if initial:
            name_entry.insert(0, initial['name'])
            type_var.set('%' if initial.get('is_percent') else '$')
            value_entry.insert(0, str(initial['value']))
            for alloc in initial['allocations']:
                self.add_allocation(alloc_parent, d, initial_alloc=alloc)

        # P0 FIX: Update surplus redirect combo when outs change
        self.update_surplus_redirect_combo()

    def delete_out(self, row):
        for d in self.out_list:
            if d['row'] == row:
                for a in d['alloc_list']:
                    a['combo'].destroy()
                    a['percent_entry'].destroy()
                    a['delete'].destroy()
                d['name_entry'].destroy()
                d['radio_dollar'].destroy()
                d['radio_percent'].destroy()
                d['value_entry'].destroy()
                d['alloc_parent'].destroy()
                d['add_alloc_button'].destroy()
                d['delete_button'].destroy()
                self.out_list.remove(d)
                break

        # Regrid remaining
        for i, d in enumerate(self.out_list):
            new_row = i + 2
            d['name_entry'].grid(row=new_row)
            d['radio_dollar'].grid(row=new_row)
            d['radio_percent'].grid(row=new_row)
            d['value_entry'].grid(row=new_row)
            d['alloc_parent'].grid(row=new_row)
            d['add_alloc_button'].grid(row=new_row)
            d['delete_button'].grid(row=new_row)
            d['row'] = new_row

        # P0 FIX: Update surplus redirect combo when outs change
        self.update_surplus_redirect_combo()

    def add_allocation(self, parent, out_d, initial_alloc=None):
        row = len(out_d['alloc_list'])

        combo = ttk.Combobox(parent, values=self.get_revenue_names())
        combo.grid(row=row, column=0)

        percent_entry = tk.Spinbox(parent, from_=0, to=100, increment=1)
        percent_entry.grid(row=row, column=1)

        delete = ttk.Button(parent, text='Delete', command=lambda r=row, p=parent: self.delete_allocation(r, p, out_d))
        delete.grid(row=row, column=2)

        d = {'combo': combo, 'percent_entry': percent_entry, 'delete': delete, 'row': row}

        out_d['alloc_list'].append(d)

        self.all_alloc_combos.append(combo)

        if initial_alloc:
            combo.set(initial_alloc['source'])
            percent_entry.insert(0, str(initial_alloc['percent']))

    def delete_allocation(self, row, parent, out_d):
        for d in out_d['alloc_list']:
            if d['row'] == row:
                d['combo'].destroy()
                d['percent_entry'].destroy()
                d['delete'].destroy()
                out_d['alloc_list'].remove(d)
                self.all_alloc_combos.remove(d['combo'])
                break

        # Regrid remaining allocations
        for i, d in enumerate(out_d['alloc_list']):
            new_row = i
            d['combo'].grid(row=new_row)
            d['percent_entry'].grid(row=new_row)
            d['delete'].grid(row=new_row)
            d['row'] = new_row

    def get_revenue_names(self):
        return [d['name_entry'].get() for d in self.revenue_list if d['name_entry'].get()]

    def setup_output_tab(self):
        # Configure the output tab to expand horizontally and vertically
        self.output_tab.columnconfigure(0, weight=1)
        # Row 0: CBO-style summary, Row 1: text panes, Row 2: graphs, Row 3+: controls/toolbar
        self.output_tab.rowconfigure(0, weight=0)
        self.output_tab.rowconfigure(1, weight=1)
        self.output_tab.rowconfigure(2, weight=3)

        # Top: Scenario summary + CBO-style summary text
        summary_frame = ttk.LabelFrame(self.output_tab, text="Scenario & CBO-Style Summary")
        summary_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=(5, 0))
        summary_frame.columnconfigure(0, weight=1)
        summary_frame.rowconfigure(0, weight=0)
        summary_frame.rowconfigure(1, weight=1)


        # Helper to format current scenario/location for display
        self.update_scenario_banner()

        # Scenario banner
        self.scenario_label = ttk.Label(
            summary_frame,
            text="Scenario: (no scenario set)",
            font=("TkDefaultFont", 9, "italic"),
            anchor="w",
        )
        self.scenario_label.grid(row=0, column=0, sticky="ew", padx=5, pady=(2, 2))

        # CBO summary text
        self.cbo_summary_text = scrolledtext.ScrolledText(summary_frame, wrap=tk.WORD, height=6)
        self.cbo_summary_text.grid(row=1, column=0, sticky="nsew")
        self.cbo_summary_text.insert(
            tk.END,
            "=== CBO-Style Budget Summary ===\nRun a baseline and proposed simulation to see a concise summary of fiscal impacts here."
        )
        self.cbo_summary_text.configure(state=tk.DISABLED)

        # Middle: comparison text area (use a horizontal PanedWindow for side-by-side)
        paned = ttk.PanedWindow(self.output_tab, orient=tk.VERTICAL)
        paned.grid(row=1, column=0, sticky="nsew")

        text_pane = ttk.PanedWindow(paned, orient=tk.HORIZONTAL)
        paned.add(text_pane, weight=1)

        # Current policy results
        current_frame = ttk.LabelFrame(text_pane, text="Current Policy Projection")
        current_frame.columnconfigure(0, weight=1)
        current_frame.rowconfigure(0, weight=1)
        current_x_scrollbar = ttk.Scrollbar(current_frame, orient=tk.HORIZONTAL)
        current_x_scrollbar.grid(row=1, column=0, sticky="ew")
        self.current_text = scrolledtext.ScrolledText(current_frame, wrap=tk.NONE, width=1, height=6, xscrollcommand=current_x_scrollbar.set)
        self.current_text.grid(row=0, column=0, sticky="nsew")
        current_x_scrollbar.config(command=self.current_text.xview)
        text_pane.add(current_frame, weight=1)

        # Proposed policy results
        proposed_frame = ttk.LabelFrame(text_pane, text="Proposed Policy Projection")
        proposed_frame.columnconfigure(0, weight=1)
        proposed_frame.rowconfigure(0, weight=1)
        proposed_x_scrollbar = ttk.Scrollbar(proposed_frame, orient=tk.HORIZONTAL)
        proposed_x_scrollbar.grid(row=1, column=0, sticky="ew")
        self.proposed_text = scrolledtext.ScrolledText(proposed_frame, wrap=tk.NONE, width=1, height=6, xscrollcommand=proposed_x_scrollbar.set)
        self.proposed_text.grid(row=0, column=0, sticky="nsew")
        proposed_x_scrollbar.config(command=self.proposed_text.xview)
        text_pane.add(proposed_frame, weight=1)

        # Bottom: graph area
        graph_frame = ttk.Frame(paned)
        paned.add(graph_frame, weight=3)
        graph_frame.columnconfigure(0, weight=1)
        graph_frame.rowconfigure(0, weight=1)

        viz_frame = ttk.LabelFrame(graph_frame, text="Comparative Analysis")
        viz_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        viz_frame.columnconfigure(0, weight=1)
        viz_frame.rowconfigure(0, weight=1)


        # Make figure taller to use more vertical space
        self.figure = Figure(figsize=(12, 10), dpi=100)
        # Adjust subplot parameters for better spacing
        self.figure.subplots_adjust(top=0.92, bottom=0.08, left=0.10, right=0.90, hspace=0.6, wspace=0.3)
        # Create subplot grid with proper spacing
        gs = self.figure.add_gridspec(2, 2, hspace=0.3, wspace=0.3)
        self.ax1 = self.figure.add_subplot(gs[0, 0])
        self.ax2 = self.figure.add_subplot(gs[0, 1])
        self.ax3 = self.figure.add_subplot(gs[1, 0])
        self.ax4 = self.figure.add_subplot(gs[1, 1])

        # Wrap the canvas in a ScrollableFrame so large figures can be scrolled
        viz_outer = ScrollableFrame(viz_frame)
        viz_outer.grid(row=0, column=0, sticky="nsew")
        viz_outer.columnconfigure(0, weight=1)
        viz_outer.rowconfigure(0, weight=1)
        viz_outer.scrollable_frame.columnconfigure(0, weight=1)
        viz_outer.scrollable_frame.rowconfigure(0, weight=1)

        self.canvas = FigureCanvasTkAgg(self.figure, master=viz_outer.scrollable_frame)
        self.canvas.draw()
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        # Set up the legend interaction handler
        def on_legend_click(event):
            if event.inaxes:
                legend = event.inaxes.get_legend()
                if legend is None:
                    return

                # Find which legend item was clicked
                for i, (legline, origtxt) in enumerate(zip(legend.get_lines(), legend.get_texts())):
                    if legline.contains(event)[0]:
                        # Toggle visibility of the corresponding line
                        visible = not legline.get_visible()
                        legline.set_visible(visible)
                        origtxt.set_alpha(1.0 if visible else 0.2)

                        # Find and toggle all matching lines across all subplots
                        label = legline.get_label()
                        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                            for line in ax.get_lines():
                                if line.get_label() == label:
                                    line.set_visible(visible)
                                    line.set_alpha(1.0 if visible else 0.2)

                        self.canvas.draw_idle()
                        break

        self.canvas.mpl_connect('button_press_event', on_legend_click)

        def on_pick(event):
            """Handle clicks on the legend to toggle series visibility."""
            if hasattr(event, 'artist'):
                if isinstance(event.artist, plt.Line2D):
                    # Get the clicked legend line
                    legline = event.artist
                    label = legline.get_label()

                    # Find all lines with this label across all subplots
                    for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
                        for line in ax.get_lines():
                            if line.get_label() == label:
                                visible = not line.get_visible()
                                line.set_visible(visible)
                                # Update legend item appearance
                                legline.set_alpha(1.0 if visible else 0.3)
                                if visible:
                                    legline.set_linewidth(2.0)
                                else:
                                    legline.set_linewidth(1.0)

                    if label in self.series_vars:
                        self.series_vars[label].set(visible)
                    self.canvas.draw_idle()

        self.canvas.mpl_connect('pick_event', on_pick)

        # Move the toolbar frame up in the hierarchy since we no longer need the series panel
        toolbar_frame = ttk.Frame(self.output_tab)
        toolbar_frame.grid(row=2, column=0, sticky="ew")
        toolbar = NavigationToolbar2Tk(self.canvas, toolbar_frame)
        toolbar.update()

        # P1: Add log scale controls for galactic-scale numbers
        controls_frame = ttk.Frame(self.output_tab)
        controls_frame.grid(row=3, column=0, sticky="ew", padx=5, pady=5)

        self.log_scale_var = tk.BooleanVar(value=False)
        log_scale_check = ttk.Checkbutton(controls_frame, text="Use Log Scale (for large numbers)",
                                          variable=self.log_scale_var, command=self.toggle_log_scale)
        log_scale_check.grid(row=0, column=0, padx=5)

        export_button = ttk.Button(controls_frame, text="Export Results to CSV", command=self.export_results)
        export_button.grid(row=0, column=1, padx=5)

        # Initialize series visibility dictionary
        self.series_vars = {}  # map column name -> tk.BooleanVar

    # (The editable 'run_simulation' for proposed policy is defined later.)

    def create_tooltip(self, widget, text):
        def enter(event):
            x, y, _, _ = widget.bbox("insert")
            x += widget.winfo_rootx() + 25
            y += widget.winfo_rooty() + 20

            self.tooltip = tk.Toplevel(widget)
            self.tooltip.wm_overrideredirect(True)
            self.tooltip.wm_geometry(f"+{x}+{y}")

            label = ttk.Label(self.tooltip, text=text, background="#ffffe0", relief="solid", borderwidth=1)
            label.pack()

        def leave(event):
            if hasattr(self, 'tooltip'):
                self.tooltip.destroy()

        widget.bind('<Enter>', enter)
        widget.bind('<Leave>', leave)

    def run_baseline_simulation(self):
        """Run simulation with current policy parameters from the Current Policy tab"""
        try:
            # Get all current values from the Current Policy tab
            current_values = self.collect_current_values()

            # Save to current_policy for future reference
            self.current_policy = deepcopy(current_values)
            df = simulate_years(
                self.current_policy['general'],
                self.current_policy['revenues'],
                self.current_policy['outs']
            )
            self.current_simulation_results = df
            self.current_text.delete(1.0, tk.END)
            self.current_text.insert(tk.END, df.to_string(index=False))
            # Populate series checkboxes so user can toggle series right away
            try:
                self.refresh_series_checkboxes()
            except Exception:
                pass

            # Mark baseline as run and enable Proposed tab in the wizard
            self.baseline_run = True
            try:
                if hasattr(self, "proposed_tab_index"):
                    self.notebook.tab(self.proposed_tab_index, state="normal")
            except Exception:
                pass
            return df
        except Exception as e:
            messagebox.showerror("Baseline Simulation Error", str(e))
            return None

    def edit_current_policy(self):
        """Setup the Current Policy tabs with editable interface similar to Proposed."""
        # Setup General tab
        self.setup_current_general_tab()

        # Setup Revenues tab
        self.setup_current_revenues_tab()

        # Setup Outs tab
        self.setup_current_outs_tab()

        # Populate with current policy data
        self.populate_current_policy_data()

    def setup_current_general_tab(self):
        """Setup the General sub-tab for Current Policy"""
        # Clear existing children
        for child in self.current_general_tab.winfo_children():
            child.destroy()

        # Configure grid weights
        self.current_general_tab.columnconfigure(0, weight=1)
        self.current_general_tab.rowconfigure(1, weight=1)

        # Controls at top
        ctrl_frame = ttk.Frame(self.current_general_tab)
        ctrl_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=3)

        # Left side - edit controls
        edit_frame = ttk.LabelFrame(ctrl_frame, text="Edit Controls")
        edit_frame.grid(row=0, column=0, padx=5, sticky="w")

        save_btn = ttk.Button(edit_frame, text="Save Current", command=self.save_current_edits)
        save_btn.grid(row=0, column=0, padx=2)
        cancel_btn = ttk.Button(edit_frame, text="Cancel", command=self.edit_current_policy)
        cancel_btn.grid(row=0, column=1, padx=2)
        copy_to_prop = ttk.Button(edit_frame, text="Copy Current → Proposed", command=self.copy_current_to_proposed)
        copy_to_prop.grid(row=0, column=2, padx=2)

        # Right side - import/export controls
        io_frame = ttk.LabelFrame(ctrl_frame, text="Import/Export")
        io_frame.grid(row=0, column=1, padx=5, sticky="w")

        import_btn = ttk.Button(io_frame, text="Import from CSV", command=self.import_current_from_csv)
        import_btn.grid(row=0, column=0, padx=2)
        export_btn = ttk.Button(io_frame, text="Export to CSV", command=self.export_current_to_csv)
        export_btn.grid(row=0, column=1, padx=2)

        # General parameters (editable)
        gen_frame = ttk.LabelFrame(self.current_general_tab, text="General Parameters (Current)")
        gen_frame.grid(row=1, column=0, sticky="nsew", padx=5, pady=5)
        gen_frame.columnconfigure(0, weight=1)

        self.current_general_entries = {}
        param_row = 0
        for key, val in self.current_policy['general'].items():
            container = ttk.Frame(gen_frame)
            container.grid(row=param_row, column=0, sticky="ew", padx=5, pady=2)
            container.columnconfigure(1, weight=1)  # Entry expands

            label = ttk.Label(container, text=key.replace('_', ' ').title() + ":")
            label.grid(row=0, column=0, sticky="w")
            entry = ttk.Entry(container)
            entry.insert(0, str(val))
            entry.grid(row=0, column=1, sticky="ew")
            self.current_general_entries[key] = entry
            param_row += 1

        # Add buttons and status label at bottom
        button_frame = ttk.Frame(self.current_general_tab)
        button_frame.grid(row=2, column=0, pady=10)

        run_button = ttk.Button(button_frame, text="Run Baseline Simulation", command=self.run_baseline_simulation)
        run_button.grid(row=0, column=0, padx=5)

        preview_button = ttk.Button(button_frame, text="Preview Flow", command=lambda: self.show_flow_preview(use_current=True))
        preview_button.grid(row=0, column=1, padx=5)

        # Status label for validation messages
        self.current_status_label = ttk.Label(self.current_general_tab, text="", foreground="red")
        self.current_status_label.grid(row=3, column=0, pady=5)

    def setup_current_revenues_tab(self):
        """Setup the Revenues sub-tab for Current Policy"""
        # Clear existing children
        for child in self.current_revenues_tab.winfo_children():
            child.destroy()

        # Configure grid weights
        self.current_revenues_tab.columnconfigure(0, weight=1)
        self.current_revenues_tab.rowconfigure(1, weight=1)

        add_button = ttk.Button(self.current_revenues_tab, text="Add Revenue", command=self.add_revenue_current)
        add_button.grid(row=0, column=0, columnspan=9, pady=5)

        self.current_revenues_container = ScrollableFrame(self.current_revenues_tab)
        self.current_revenues_container.grid(row=1, column=0, sticky='nsew', padx=2, pady=2)

        # Configure columns with specific weights for proper alignment
        self.current_revenues_container.scrollable_frame.columnconfigure(0, weight=2, minsize=120)  # Name
        self.current_revenues_container.scrollable_frame.columnconfigure(1, weight=0, minsize=30)   # $ radio
        self.current_revenues_container.scrollable_frame.columnconfigure(2, weight=0, minsize=30)   # % radio
        self.current_revenues_container.scrollable_frame.columnconfigure(3, weight=0, minsize=80)   # Value
        self.current_revenues_container.scrollable_frame.columnconfigure(4, weight=3, minsize=150)  # Description
        self.current_revenues_container.scrollable_frame.columnconfigure(5, weight=0, minsize=100)  # Alloc Health
        self.current_revenues_container.scrollable_frame.columnconfigure(6, weight=0, minsize=100)  # Alloc States
        self.current_revenues_container.scrollable_frame.columnconfigure(7, weight=0, minsize=100)  # Alloc Federal
        self.current_revenues_container.scrollable_frame.columnconfigure(8, weight=0, minsize=60)   # Delete

        # Add header row inside the scrollable frame
        header_parent = self.current_revenues_container.scrollable_frame
        ttk.Label(header_parent, text="Name", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Type", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=1, columnspan=2, sticky='ew', pady=2)
        ttk.Label(header_parent, text="Value", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=3, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Description", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=4, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Alloc Health (%)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=5, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Alloc States (%)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=6, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Alloc Federal (%)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=7, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Actions", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=8, sticky='ew', padx=2, pady=2)

    def setup_current_outs_tab(self):
        """Setup the Outs sub-tab for Current Policy"""
        # Clear existing children
        for child in self.current_outs_tab.winfo_children():
            child.destroy()

        # Configure grid weights
        self.current_outs_tab.columnconfigure(0, weight=1)
        self.current_outs_tab.rowconfigure(1, weight=1)

        add_out_btn = ttk.Button(self.current_outs_tab, text="Add Out Category", command=self.add_out_current)
        add_out_btn.grid(row=0, column=0, columnspan=9, pady=5)

        self.current_outs_container = ScrollableFrame(self.current_outs_tab)
        self.current_outs_container.grid(row=1, column=0, sticky='nsew', padx=2, pady=2)

        # Configure columns with specific weights for proper alignment
        self.current_outs_container.scrollable_frame.columnconfigure(0, weight=2, minsize=120)  # Name
        self.current_outs_container.scrollable_frame.columnconfigure(1, weight=0, minsize=30)   # $ radio
        self.current_outs_container.scrollable_frame.columnconfigure(2, weight=0, minsize=30)   # % radio
        self.current_outs_container.scrollable_frame.columnconfigure(3, weight=0, minsize=100)  # Value
        self.current_outs_container.scrollable_frame.columnconfigure(4, weight=3, minsize=200)  # Allocations
        self.current_outs_container.scrollable_frame.columnconfigure(5, weight=0, minsize=100)  # Add Alloc button
        self.current_outs_container.scrollable_frame.columnconfigure(6, weight=0, minsize=60)   # Delete

        # Add header row inside the scrollable frame
        header_parent = self.current_outs_container.scrollable_frame
        ttk.Label(header_parent, text="Name", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=0, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Type", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=1, columnspan=2, sticky='ew', pady=2)
        ttk.Label(header_parent, text="Value (target)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=3, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Allocations (add below)", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=4, sticky='ew', padx=2, pady=2)
        ttk.Label(header_parent, text="Actions", font=('TkDefaultFont', 9, 'bold')).grid(row=0, column=5, columnspan=2, sticky='ew', padx=2, pady=2)

    def populate_current_policy_data(self):
        """Populate the Current Policy tabs with data"""
        # Clear existing widgets first
        for d in list(self.current_revenue_list):
            for widget_key in ['name_entry', 'radio_dollar', 'radio_percent', 'value_entry', 'desc_entry',
                              'alloc_health_entry', 'alloc_states_entry', 'alloc_federal_entry', 'delete_button', 'sep']:
                if widget_key in d:
                    try:
                        d[widget_key].destroy()
                    except Exception:
                        pass

        for d in list(self.current_out_list):
            for widget_key in ['name_entry', 'radio_dollar', 'radio_percent', 'value_entry', 'delete_button',
                              'add_alloc_button', 'alloc_frame', 'sep']:
                if widget_key in d:
                    try:
                        d[widget_key].destroy()
                    except Exception:
                        pass

        # Clear lists
        self.current_revenue_list = []
        self.current_out_list = []

        # Populate revenues
        for rev in deepcopy(self.current_policy['revenues']):
            self.add_revenue_current(initial=rev)

        # Populate outs
        for out in deepcopy(self.current_policy['outs']):
            self.add_out_current(initial=out)

    def add_revenue_current(self, initial=None):
        row = len(self.current_revenue_list)
        parent = self.current_revenues_container.scrollable_frame

        # Account for header row at row 0, data starts at row 1
        # Each data item takes 2 rows (separator + data)
        grid_row = 1 + row * 2

        sep = ttk.Separator(parent, orient='horizontal')
        sep.grid(row=grid_row, column=0, columnspan=9, sticky='ew', pady=3)

        name_entry = ttk.Entry(parent)
        name_entry.grid(row=grid_row+1, column=0, sticky='ew', padx=2)

        type_var = tk.StringVar(value='$')
        radio_dollar = ttk.Radiobutton(parent, text='$', variable=type_var, value='$')
        radio_dollar.grid(row=grid_row+1, column=1)
        radio_percent = ttk.Radiobutton(parent, text='%', variable=type_var, value='%')
        radio_percent.grid(row=grid_row+1, column=2)

        value_entry = ttk.Entry(parent)
        value_entry.grid(row=grid_row+1, column=3, padx=2)

        desc_entry = ttk.Entry(parent)
        desc_entry.grid(row=grid_row+1, column=4, sticky="ew", padx=2)

        alloc_health_entry = tk.Spinbox(parent, from_=0, to=100, increment=0.1, format="%.1f")
        alloc_health_entry.grid(row=grid_row+1, column=5, padx=2)
        alloc_health_entry.bind('<KeyRelease>', lambda e: self.validate_current_allocations())

        alloc_states_entry = tk.Spinbox(parent, from_=0, to=100, increment=0.1, format="%.1f")
        alloc_states_entry.grid(row=grid_row+1, column=6, padx=2)
        alloc_states_entry.bind('<KeyRelease>', lambda e: self.validate_current_allocations())

        alloc_federal_entry = tk.Spinbox(parent, from_=0, to=100, increment=0.1, format="%.1f")
        alloc_federal_entry.grid(row=grid_row+1, column=7, padx=2)
        alloc_federal_entry.bind('<KeyRelease>', lambda e: self.validate_current_allocations())

        delete_button = ttk.Button(parent, text='Delete', command=lambda r=row: self.delete_revenue_current(r))
        delete_button.grid(row=grid_row+1, column=8, padx=2)

        d = {'name_entry': name_entry, 'type_var': type_var, 'value_entry': value_entry, 'desc_entry': desc_entry,
            'alloc_health_entry': alloc_health_entry, 'alloc_states_entry': alloc_states_entry, 'alloc_federal_entry': alloc_federal_entry,
            'radio_dollar': radio_dollar, 'radio_percent': radio_percent, 'delete_button': delete_button, 'row': row, 'sep': sep}

        self.current_revenue_list.append(d)

        if initial:
            name_entry.insert(0, initial['name'])
            type_var.set('%' if initial.get('is_percent') else '$')
            value_entry.insert(0, str(initial['value']))
            desc_entry.insert(0, initial.get('desc',''))
            # For spinboxes, delete existing content first to avoid concatenation
            alloc_health_entry.delete(0, tk.END)
            alloc_health_entry.insert(0, str(initial.get('alloc_health',0)))
            alloc_states_entry.delete(0, tk.END)
            alloc_states_entry.insert(0, str(initial.get('alloc_states',0)))
            alloc_federal_entry.delete(0, tk.END)
            alloc_federal_entry.insert(0, str(initial.get('alloc_federal',0)))

    def delete_revenue_current(self, row):
        for d in self.current_revenue_list:
            if d['row'] == row:
                for widget in [d['name_entry'], d['radio_dollar'], d['radio_percent'], d['value_entry'], d['desc_entry'], d['alloc_health_entry'], d['alloc_states_entry'], d['alloc_federal_entry'], d['delete_button']]:
                    try:
                        widget.destroy()
                    except Exception:
                        pass
                try:
                    d['sep'].destroy()
                except Exception:
                    pass
                self.current_revenue_list.remove(d)
                break

        # Regrid remaining
        for i, d in enumerate(self.current_revenue_list):
            new_row = i + 2
            d['name_entry'].grid(row=new_row)
            d['radio_dollar'].grid(row=new_row)
            d['radio_percent'].grid(row=new_row)
            d['value_entry'].grid(row=new_row)
            d['desc_entry'].grid(row=new_row)
            d['alloc_health_entry'].grid(row=new_row)
            d['alloc_states_entry'].grid(row=new_row)
            d['alloc_federal_entry'].grid(row=new_row)
            d['delete_button'].grid(row=new_row)
            d['row'] = new_row

    def add_out_current(self, initial=None):
        row = len(self.current_out_list)
        parent = self.current_outs_container.scrollable_frame

        # Account for header row at row 0, data starts at row 1
        grid_row = 1 + row * 2

        sep = ttk.Separator(parent, orient='horizontal')
        sep.grid(row=grid_row, column=0, columnspan=7, sticky='ew', pady=3)

        name_entry = ttk.Entry(parent)
        name_entry.grid(row=grid_row+1, column=0, sticky='ew', padx=2)

        type_var = tk.StringVar(value='$')
        radio_dollar = ttk.Radiobutton(parent, text='$', variable=type_var, value='$')
        radio_dollar.grid(row=grid_row+1, column=1)
        radio_percent = ttk.Radiobutton(parent, text='%', variable=type_var, value='%')
        radio_percent.grid(row=grid_row+1, column=2)

        value_entry = ttk.Entry(parent)
        value_entry.grid(row=grid_row+1, column=3, padx=2)

        alloc_parent = ttk.Frame(parent)
        alloc_parent.grid(row=grid_row+1, column=4, rowspan=1, sticky="nsew", padx=2)

        # Create placeholder button - will update command after d is created
        add_alloc_button = ttk.Button(parent, text='Add Allocation')
        add_alloc_button.grid(row=grid_row+1, column=5, padx=2)

        delete_button = ttk.Button(parent, text='Delete', command=lambda r=row: self.delete_out_current(r))
        delete_button.grid(row=grid_row+1, column=6, padx=2)

        d = {'name_entry': name_entry, 'type_var': type_var, 'value_entry': value_entry, 'alloc_parent': alloc_parent, 'add_alloc_button': add_alloc_button, 'delete_button': delete_button, 'row': row, 'alloc_list': [], 'radio_dollar': radio_dollar, 'radio_percent': radio_percent, 'sep': sep}

        # Now configure the button command with the correct d reference
        add_alloc_button.config(command=lambda p=alloc_parent, out_d=d: self.add_allocation_current(p, out_d))

        self.current_out_list.append(d)

        if initial:
            name_entry.insert(0, initial['name'])
            type_var.set('%' if initial.get('is_percent') else '$')
            value_entry.insert(0, str(initial['value']))
            for alloc in initial.get('allocations', []):
                self.add_allocation_current(alloc_parent, d, initial_alloc=alloc)

    def delete_out_current(self, row):
        for d in self.current_out_list:
            if d['row'] == row:
                try:
                    for a in d['alloc_list']:
                        a['combo'].destroy()
                        a['percent_entry'].destroy()
                        a['delete'].destroy()
                except Exception:
                    pass
                for w in ['name_entry', 'radio_dollar', 'radio_percent', 'value_entry', 'alloc_parent', 'add_alloc_button', 'delete_button']:
                    try:
                        widget = d.get(w)
                        if widget:
                            widget.destroy()
                    except Exception:
                        pass
                try:
                    d['sep'].destroy()
                except Exception:
                    pass
                try:
                    self.current_out_list.remove(d)
                except ValueError:
                    pass
                break

        # Regrid remaining
        for i, d in enumerate(self.current_out_list):
            new_row = i + 2
            d['name_entry'].grid(row=new_row)
            d['radio_dollar'].grid(row=new_row)
            d['radio_percent'].grid(row=new_row)
            d['value_entry'].grid(row=new_row)
            d['alloc_parent'].grid(row=new_row)
            d['add_alloc_button'].grid(row=new_row)
            d['delete_button'].grid(row=new_row)
            d['row'] = new_row

    def add_allocation_current(self, parent, out_d, initial_alloc=None):
        row = len(out_d['alloc_list'])

        combo = ttk.Combobox(parent, values=self.get_revenue_names_current())
        combo.grid(row=row, column=0)

        percent_entry = tk.Spinbox(parent, from_=0, to=100, increment=1)
        percent_entry.grid(row=row, column=1)
        percent_entry.bind('<KeyRelease>', lambda e: self.validate_current_allocations())

        delete = ttk.Button(parent, text='Delete', command=lambda r=row, p=parent: self.delete_allocation_current(r, p, out_d))
        delete.grid(row=row, column=2)

        d = {'combo': combo, 'percent_entry': percent_entry, 'delete': delete, 'row': row}

        out_d['alloc_list'].append(d)

        if initial_alloc:
            combo.set(initial_alloc.get('source'))
            percent_entry.delete(0, 'end')
            percent_entry.insert(0, str(initial_alloc.get('percent')))

    def delete_allocation_current(self, row, parent, out_d):
        for d in out_d['alloc_list']:
            if d['row'] == row:
                d['combo'].destroy()
                d['percent_entry'].destroy()
                d['delete'].destroy()
                out_d['alloc_list'].remove(d)
                break

    def get_revenue_names_current(self):
        return [d['name_entry'].get() for d in self.current_revenue_list if d['name_entry'].get()]

    def save_current_edits(self):
        try:
            # First validate all allocations
            if not self.validate_current_allocations():
                return  # Don't save if validation fails

            # Collect general parameters
            new_general = {}
            for key, entry in self.current_general_entries.items():
                try:
                    val_str = entry.get().strip()
                    new_general[key] = float(val_str)
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid value for {key}: '{entry.get()}' - {e}")
                    return

            new_revenues = []
            for d in self.current_revenue_list:
                try:
                    # Clean up spinbox values that might have formatting issues
                    alloc_health_str = d['alloc_health_entry'].get().strip()
                    alloc_states_str = d['alloc_states_entry'].get().strip()
                    alloc_federal_str = d['alloc_federal_entry'].get().strip()

                    rev_name = d['name_entry'].get()

                    # Try to convert each value with detailed error reporting
                    try:
                        value = float(d['value_entry'].get() or 0)
                    except ValueError as ve:
                        messagebox.showerror("Error", f"Invalid value for revenue '{rev_name}': '{d['value_entry'].get()}' - {ve}")
                        return

                    try:
                        alloc_health = float(alloc_health_str or 0)
                    except ValueError as ve:
                        messagebox.showerror("Error", f"Invalid health allocation for revenue '{rev_name}': '{alloc_health_str}' - {ve}")
                        return

                    try:
                        alloc_states = float(alloc_states_str or 0)
                    except ValueError as ve:
                        messagebox.showerror("Error", f"Invalid states allocation for revenue '{rev_name}': '{alloc_states_str}' - {ve}")
                        return

                    try:
                        alloc_federal = float(alloc_federal_str or 0)
                    except ValueError as ve:
                        messagebox.showerror("Error", f"Invalid federal allocation for revenue '{rev_name}': '{alloc_federal_str}' - {ve}")
                        return

                    rev = {
                        'name': rev_name,
                        'is_percent': d['type_var'].get() == '%',
                        'value': value,
                        'desc': d['desc_entry'].get(),
                        'alloc_health': alloc_health,
                        'alloc_states': alloc_states,
                        'alloc_federal': alloc_federal,
                    }
                    new_revenues.append(rev)
                except Exception as e:
                    messagebox.showerror("Error", f"Unexpected error processing revenue '{d['name_entry'].get()}': {e}")
                    return

            new_outs = []
            for d in self.current_out_list:
                try:
                    allocations = []
                    for a in d['alloc_list']:
                        percent_str = a['percent_entry'].get().strip()
                        allocations.append({'source': a['combo'].get(), 'percent': float(percent_str or 0)})
                    out = {'name': d['name_entry'].get(), 'is_percent': d['type_var'].get() == '%', 'value': float(d['value_entry'].get() or 0), 'allocations': allocations}
                    new_outs.append(out)
                except ValueError as e:
                    messagebox.showerror("Error", f"Invalid out value for {d['name_entry'].get()}: {e}")
                    return

            # Additional validation is already done by validate_current_allocations() at the start
            # No need for validate_allocations_from_widgets here

            self.current_policy = {'general': deepcopy(new_general), 'revenues': deepcopy(new_revenues), 'outs': deepcopy(new_outs)}
            self.populate_current_policy_data()
            self.run_baseline_simulation()
            messagebox.showinfo("Success", "Current policy updated.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to save current edits: {e}")

    def clear_proposed_ui(self):
        """Remove all widgets from the proposed editors and clear lists"""
        # Destroy revenue widgets
        for d in list(self.revenue_list):
            for w in ['name_entry', 'radio_dollar', 'radio_percent', 'value_entry', 'desc_entry', 'alloc_health_entry', 'alloc_states_entry', 'alloc_federal_entry', 'delete_button']:
                try:
                    widget = d.get(w)
                    if widget:
                        widget.destroy()
                except Exception:
                    pass
            try:
                self.revenue_list.remove(d)
            except ValueError:
                pass

        # Destroy out widgets
        for d in list(self.out_list):
            try:
                for a in d['alloc_list']:
                    a['combo'].destroy()
                    a['percent_entry'].destroy()
                    a['delete'].destroy()
            except Exception:
                pass
            for w in ['name_entry', 'radio_dollar', 'radio_percent', 'value_entry', 'alloc_parent', 'add_alloc_button', 'delete_button']:
                try:
                    widget = d.get(w)
                    if widget:
                        widget.destroy()
                except Exception:
                    pass
            try:
                self.out_list.remove(d)
            except ValueError:
                pass

    def copy_current_to_proposed(self):
        """Replace proposed editors with a copy of current policy"""
        self.clear_proposed_ui()
        # Copy general
        for k, entry in self.general_entries.items():
            entry.delete(0, tk.END)
            entry.insert(0, str(self.current_policy['general'].get(k, '')))

        # Copy revenues and outs into proposed UI
        for rev in deepcopy(self.current_policy['revenues']):
            self.add_revenue(initial=rev)
        for out in deepcopy(self.current_policy['outs']):
            self.add_out(initial=out)

    def copy_proposed_to_current(self):
        """Read proposed editor values and set them as current policy"""
        try:
            new_general = {}
            for key, entry in self.general_entries.items():
                new_general[key] = float(entry.get())

            new_revenues = []
            for d in self.revenue_list:
                rev = {
                    'name': d['name_entry'].get(),
                    'is_percent': d['type_var'].get() == '%',
                    'value': float(d['value_entry'].get()),
                    'desc': d['desc_entry'].get(),
                    'alloc_health': float(d['alloc_health_entry'].get() or 0),
                    'alloc_states': float(d['alloc_states_entry'].get() or 0),
                    'alloc_federal': float(d['alloc_federal_entry'].get() or 0),
                }
                new_revenues.append(rev)

            new_outs = []
            for d in self.out_list:
                allocations = []
                for a in d['alloc_list']:
                    allocations.append({'source': a['combo'].get(), 'percent': float(a['percent_entry'].get())})
                out = {'name': d['name_entry'].get(), 'is_percent': d['type_var'].get() == '%', 'value': float(d['value_entry'].get()), 'allocations': allocations}
                new_outs.append(out)

            # Set as current policy
            self.current_policy = {'general': deepcopy(new_general), 'revenues': deepcopy(new_revenues), 'outs': deepcopy(new_outs)}
            self.populate_current_policy_data()
            self.run_baseline_simulation()
            messagebox.showinfo("Success", "Proposed policy copied to Current baseline.")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to copy proposed to current: {e}")

    def load_policy_from_excel(self):
        """Load baseline/current policy from an Excel file with sheets: General, Revenues, Outs
        Revenues sheet must have columns: name,is_percent,value,desc,alloc_health,alloc_states,alloc_federal
        Outs sheet should have columns: name,is_percent,value,allocations (allocations can be JSON list)
        """
        path = filedialog.askopenfilename(filetypes=[("Excel files","*.xlsx;*.xls")])
        if not path:
            return
        try:
            xls = pd.read_excel(path, sheet_name=None)
        except Exception as e:
            messagebox.showerror("Load Error", f"Failed to read Excel: {e}")
            return

        new_general = deepcopy(self.current_policy['general'])
        new_revenues = deepcopy(self.current_policy['revenues'])
        new_outs = deepcopy(self.current_policy['outs'])

        # General
        if 'General' in xls:
            dfg = xls['General']
            # Expect key/value layout
            try:
                if dfg.shape[1] >= 2:
                    for _, row in dfg.iterrows():
                        key = str(row.iloc[0])
                        val = row.iloc[1]
                        # attempt numeric conversion
                        try:
                            val = float(val)
                        except Exception:
                            pass
                        new_general[key] = val
            except Exception:
                pass

        # Revenues
        if 'Revenues' in xls:
            dfr = xls['Revenues']
            new_revenues = []
            for _, row in dfr.iterrows():
                try:
                    rev = {
                        'name': row['name'],
                        'is_percent': bool(row.get('is_percent', False)),
                        'value': float(row.get('value', 0)),
                        'desc': row.get('desc', ''),
                        'alloc_health': float(row.get('alloc_health', 0)),
                        'alloc_states': float(row.get('alloc_states', 0)),
                        'alloc_federal': float(row.get('alloc_federal', 0)),
                    }
                    new_revenues.append(rev)
                except Exception:
                    continue

        # Outs
        if 'Outs' in xls:
            dfo = xls['Outs']
            new_outs = []
            for _, row in dfo.iterrows():
                try:
                    allocations = []
                    if 'allocations' in row and not pd.isna(row['allocations']):
                        import ast
                        try:
                            allocations = ast.literal_eval(row['allocations'])
                        except Exception:
                            allocations = []
                    out = {
                        'name': row['name'],
                        'is_percent': bool(row.get('is_percent', False)),
                        'value': float(row.get('value', 0)),
                        'allocations': allocations,
                    }
                    new_outs.append(out)
                except Exception:
                    continue

    def refresh_comparison_scenario_combos(self):
        """Populate the left/right scenario comparison dropdowns on the Comparison tab."""
        names = list(self.scenarios.keys())
        if hasattr(self, "compare_left_combo"):
            self.compare_left_combo["values"] = names
            if names and not self.compare_left_var.get():
                self.compare_left_var.set(names[0])
        if hasattr(self, "compare_right_combo"):
            self.compare_right_combo["values"] = names
            if len(names) > 1 and not self.compare_right_var.get():
                self.compare_right_var.set(names[1])

        # Note: applying imported Excel policy to current configuration is handled elsewhere.
        # This helper focuses only on keeping the comparison dropdowns in sync.

    def run_simulation(self):
        """Run simulation with proposed policy changes"""
        try:
            # First run baseline using current tab values
            df_current = None
            current_values = self.collect_current_values()

            # Run current policy simulation
            df_current = simulate_years(
                current_values['general'],
                current_values['revenues'],
                current_values['outs']
            )
            self.current_simulation_results = df_current
            self.current_text.delete(1.0, tk.END)
            self.current_text.insert(tk.END, df_current.to_string(index=False))

            # Mark proposed as "ready" and enable Comparison tab, since both sides are computed
            self.proposed_run = True
            try:
                if hasattr(self, "comparison_tab_index"):
                    self.notebook.tab(self.comparison_tab_index, state="normal")
            except Exception:
                pass

            # Then get proposed values
            internal_general = {}
            for key, entry in self.general_entries.items():
                # Handle surplus_redirect_target as string, others as float
                if key == 'surplus_redirect_target':
                    internal_general[key] = entry.get()
                else:
                    try:
                        value = float(entry.get() or 0)
                    except ValueError:
                        value = 0.0
                    internal_general[key] = value

            # Collect proposed revenues and allow loose totals for rapid testing
            validation_warnings = []

            internal_revenues = []
            for d in self.revenue_list:
                name = d['name_entry'].get()
                if not name:
                    raise ValueError("All revenues must have a name.")
                rev = {
                    'name': name,
                    'is_percent': d['type_var'].get() == '%',
                    'value': float(d['value_entry'].get()),
                    'desc': d['desc_entry'].get(),
                    'alloc_health': float(d['alloc_health_entry'].get()),
                    'alloc_states': float(d['alloc_states_entry'].get()),
                    'alloc_federal': float(d['alloc_federal_entry'].get()),
                }
                total_alloc = rev['alloc_health'] + rev['alloc_states'] + rev['alloc_federal']
                if total_alloc > 100.001:
                    validation_warnings.append(
                        f"WARNING: {name} revenue allocations exceed 100% (currently {total_alloc:.1f}%)."
                    )
                elif total_alloc < 99.9:  # Allow small rounding errors
                    validation_warnings.append(
                        f"WARNING: {name} revenue allocations are under 100% (currently {total_alloc:.1f}%)."
                    )
                internal_revenues.append(rev)

            # Collect proposed outs and track how much of each revenue is allocated
            internal_outs = []
            rev_alloced = {rev['name']: 0 for rev in internal_revenues}
            for d in self.out_list:
                name = d['name_entry'].get()
                if not name:
                    raise ValueError("All out categories must have a name.")
                allocations = []
                for a in d['alloc_list']:
                    source = a['combo'].get()
                    percent = float(a['percent_entry'].get())
                    allocations.append({'source': source, 'percent': percent})
                    if source in rev_alloced:
                        rev_alloced[source] += percent
                out = {
                    'name': name,
                    'is_percent': d['type_var'].get() == '%',
                    'value': float(d['value_entry'].get()),
                    'allocations': allocations,
                }
                internal_outs.append(out)

            # Validation: warn (but do not block) if any revenue is over- or under-allocated
            for rev_name, percent in rev_alloced.items():
                if percent > 100.001:
                    validation_warnings.append(
                        f"WARNING: Total allocation from {rev_name} exceeds 100% (currently {percent:.1f}%)."
                    )
                elif percent < 99.9:
                    validation_warnings.append(
                        f"WARNING: {rev_name} is under-allocated ({percent:.1f}% used, {100-percent:.1f}% unallocated)."
                    )

            # Show warnings but allow simulation to continue for rapid experimentation
            if validation_warnings:
                warning_msg = "\n".join(validation_warnings) + "\n\nThis may result in over- or under-funding. Continue?"
                if not messagebox.askyesno("Allocation Warning", warning_msg):
                    return

            df_proposed = simulate_years(internal_general, internal_revenues, internal_outs)
            self.proposed_text.delete(1.0, tk.END)
            self.proposed_text.insert(tk.END, df_proposed.to_string(index=False))

            # Update visualizations
            self.update_comparison_plots(self.current_simulation_results, df_proposed)

            # Store for later use (plots, exports, etc.)
            self.df = df_proposed

            # Compute and display CBO-style summary
            try:
                summary_text, summary_table = calculate_cbo_summary(self.current_simulation_results, df_proposed)
                self.cbo_summary_text.configure(state=tk.NORMAL)
                self.cbo_summary_text.delete(1.0, tk.END)
                self.cbo_summary_text.insert(tk.END, summary_text)
                self.cbo_summary_text.configure(state=tk.DISABLED)
                self.cbo_summary_table = summary_table
            except Exception:
                # Fail gracefully; core simulation should still work
                self.cbo_summary_table = None

            # Refresh the series checkboxes so they reflect the new data
            try:
                self.refresh_series_checkboxes()
            except Exception:
                pass

        except ValueError as e:
            messagebox.showerror("Input Error", str(e))

    def toggle_log_scale(self):
        """
        P1: Toggle between linear and logarithmic scale for plots.
        Essential for galactic-scale numbers (e.g., GDP > 10^30).
        """
        use_log = self.log_scale_var.get()

        for ax in [self.ax1, self.ax2, self.ax3, self.ax4]:
            if use_log:
                ax.set_yscale('log')
            else:
                ax.set_yscale('linear')

        self.canvas.draw()

    def collect_current_values(self):
        """Collect all values from the Current Policy tab's UI controls"""
        new_general = {}
        for key, entry in self.current_general_entries.items():
            try:
                val = float(entry.get() or 0)
            except (ValueError, AttributeError):
                val = 0.0
            new_general[key] = val

        new_revenues = []
        for d in self.current_revenue_list:
            try:
                rev = {
                    'name': d['name_entry'].get() or '',
                    'is_percent': d['type_var'].get() == '%',
                    'value': float(d['value_entry'].get() or 0),
                    'desc': d['desc_entry'].get() or '',
                    'alloc_health': float(d['alloc_health_entry'].get() or 0),
                    'alloc_states': float(d['alloc_states_entry'].get() or 0),
                    'alloc_federal': float(d['alloc_federal_entry'].get() or 0),
                }
                new_revenues.append(rev)
            except (ValueError, AttributeError):
                continue

        new_outs = []
        for d in self.current_out_list:
            try:
                allocations = []
                for a in d['alloc_list']:
                    try:
                        allocations.append({
                            'source': a['combo'].get() or '',
                            'percent': float(a['percent_entry'].get() or 0)
                        })
                    except (ValueError, AttributeError):
                        continue
                out = {
                    'name': d['name_entry'].get() or '',
                    'is_percent': d['type_var'].get() == '%',
                    'value': float(d['value_entry'].get() or 0),
                    'allocations': allocations
                }
                new_outs.append(out)
            except (ValueError, AttributeError):
                continue

        return {'general': new_general, 'revenues': new_revenues, 'outs': new_outs}

    def validate_current_allocations(self):
        """Lightweight validation for current policy allocations.

        For rapid testing we only show warnings in the status label and do not
        hard-block the user unless values are non-numeric.
        """
        try:
            messages = []

            # Validate revenue allocations (health + states + federal ~ 100%)
            for d in self.current_revenue_list:
                name = d['name_entry'].get()
                if not name:
                    continue
                health = float(d['alloc_health_entry'].get() or 0)
                states = float(d['alloc_states_entry'].get() or 0)
                federal = float(d['alloc_federal_entry'].get() or 0)
                total = health + states + federal
                if total > 100.001:
                    messages.append(f"{name} allocations sum to {total:.1f}% (> 100%).")
                elif total < 99.9:
                    messages.append(f"{name} allocations sum to {total:.1f}% (< 100%).")

            # Validate out category allocations (total per revenue source ~ 100%)
            rev_alloced = {}
            for d in self.current_out_list:
                name = d['name_entry'].get()
                if not name:
                    continue
                for a in d['alloc_list']:
                    source = a['combo'].get()
                    if not source:
                        continue
                    percent = float(a['percent_entry'].get() or 0)
                    rev_alloced[source] = rev_alloced.get(source, 0) + percent

            for source, total in rev_alloced.items():
                if total > 100.001:
                    messages.append(f"Total allocation from {source} is {total:.1f}% (> 100%).")
                elif total < 99.9:
                    messages.append(f"Total allocation from {source} is {total:.1f}% (< 100%).")

            if messages:
                self.current_status_label.config(text="; ".join(messages))
            else:
                self.current_status_label.config(text="")

            # Always return True so the user is not blocked while editing
            return True
        except Exception as e:
            self.current_status_label.config(text=f"Error: Invalid input - {str(e)}")
            return False

    def update_comparison_plots(self, df_current, df_proposed):
        """Update both plots with comparison data"""
        # Clear previous plots
        self.ax1.clear()
        self.ax2.clear()
        self.ax3.clear()
        self.ax4.clear()

        # Plot 1: Multiple-series comparison (Debt, GDP, and select surpluses)
        years_c = df_current['Year']
        years_p = df_proposed['Year']

        # Helper to check if a series should be plotted
        def should_plot(col_name):
            if not self.series_vars:
                return True
            var = self.series_vars.get(col_name)
            return var.get() if var else True

        # Prepare columns to plot: GDP, Remaining Debt, Total Surplus, and all surplus columns
        cols_to_try = []
        for key in ['GDP', 'Remaining Debt', 'Total Surplus']:
            if key in df_current.columns and key in df_proposed.columns:
                cols_to_try.append(key)

        surplus_cols = [c for c in df_current.columns if 'surplus' in c.lower() and c in df_proposed.columns]
        # Avoid duplicating 'Total Surplus' if it's already included
        surplus_cols = [c for c in surplus_cols if c not in cols_to_try]
        cols_to_try.extend(surplus_cols)

        # Use the new colormaps API
        colormap = plt.colormaps['tab10']
        for i, col in enumerate(cols_to_try):
            color = colormap(i % 10)
            if not should_plot(col):
                continue
            # plot current on left, proposed on right
            if col in df_current.columns:
                self.ax1.plot(years_c, df_current[col], linestyle='-', color=color, marker='o', label=str(col), alpha=0.8)
            if col in df_proposed.columns:
                self.ax2.plot(years_p, df_proposed[col], linestyle='-', color=color, marker='o', label=str(col), alpha=0.8)

        # Set up first plot
        self.ax1.set_title('Current Policy Projection')
        self.ax1.set_xlabel('Year')
        self.ax1.set_ylabel('Trillions $')
        self.ax1.grid(True)
        legend1 = self.ax1.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=8)
        legend1.set_visible(True)  # Force legend to be visible
        for legline in legend1.get_lines():
            legline.set_picker(5)

        # Set up second plot
        self.ax2.set_title('Proposed Policy Projection')
        self.ax2.set_xlabel('Year')
        self.ax2.set_ylabel('Trillions $')
        self.ax2.grid(True)
        legend2 = self.ax2.legend(loc='upper center', bbox_to_anchor=(0.5, -0.05), ncol=3, fontsize=8)
        legend2.set_visible(True)  # Force legend to be visible
        for legline in legend2.get_lines():
            legline.set_picker(5)

        # Plot revenue breakdowns on ax3/ax4 (if present)
        revenue_cols = [c for c in df_current.columns if c.endswith(' Revenue') and c in df_proposed.columns]
        if revenue_cols:
            for i, col in enumerate(revenue_cols):
                color = colormap((i + 5) % 10)
                if not should_plot(col):
                    continue
                if col in df_current.columns:
                    self.ax3.plot(years_c, df_current[col], linestyle='-', color=color, marker='s', label=col, alpha=0.8)
                if col in df_proposed.columns:
                    self.ax4.plot(years_p, df_proposed[col], linestyle='-', color=color, marker='s', label=col, alpha=0.8)

            self.ax3.set_title('Current Revenues')
            self.ax3.set_xlabel('Year')
            self.ax3.set_ylabel('Trillions $')
            self.ax3.grid(True)
            legend3 = self.ax3.legend(loc='upper center', bbox_to_anchor=(0.5, -0.3), ncol=3, fontsize=8)
            if legend3:
                legend3.set_visible(True)  # Explicitly set legend visible
                for legline in legend3.get_lines():
                    legline.set_picker(5)

            self.ax4.set_title('Proposed Revenues')
            self.ax4.set_xlabel('Year')
            self.ax4.set_ylabel('Trillions $')
            self.ax4.grid(True)
            legend4 = self.ax4.legend(loc='upper center', bbox_to_anchor=(0.5, -0.3), ncol=3, fontsize=8)
            if legend4:
                legend4.set_visible(True)  # Explicitly set legend visible
                for legline in legend4.get_lines():
                    legline.set_picker(5)

        # Skip tight_layout and just use subplots_adjust for more control
        self.figure.subplots_adjust(
            top=0.95,      # Move plots down from top
            bottom=0.15,   # Leave room at bottom
            hspace=1.0,    # Space between plot rows
            wspace=0.3,    # Space between plot columns
            left=0.1,      # Left margin
            right=0.9      # Right margin
        )

        self.canvas.draw()

    def refresh_series_checkboxes(self):
        """Populate the series visibility panel from current/proposed DataFrames"""
        # clear existing
        for child in self.series_panel.winfo_children():
            # keep first two widgets (Refresh and Apply)
            try:
                if isinstance(child, ttk.Button):
                    continue
                child.destroy()
            except Exception:
                pass

        # gather columns from baseline and proposed
        cols = set()
        if getattr(self, 'current_simulation_results', None) is not None:
            cols.update(self.current_simulation_results.columns.tolist())
        if getattr(self, 'df', None) is not None:
            cols.update(self.df.columns.tolist())
        # Build an ordered list of columns with preferred ordering
        preferred = ['GDP', 'Remaining Debt', 'Total Surplus']
        surplus_cols = sorted([c for c in cols if 'surplus' in c.lower() and c not in preferred])
        revenue_cols = sorted([c for c in cols if c.endswith(' Revenue')])
        other_cols = sorted([c for c in cols if c not in preferred + surplus_cols + revenue_cols])

        ordered = [c for c in preferred if c in cols] + surplus_cols + revenue_cols + other_cols

        # Place checkboxes in a vertical list; default to True so items show unless user unchecks
        row = 1
        for col in ordered:
            var = self.series_vars.get(col, tk.BooleanVar(value=True))
            cb = ttk.Checkbutton(self.series_panel, text=col, variable=var, command=lambda c=col: self.apply_series_selection())
            cb.grid(row=row, column=0, sticky='w', padx=2)
            self.series_vars[col] = var
            row += 1

    def apply_series_selection(self):
        """Re-draw the comparison plots with the current series_vars selection"""
        if getattr(self, 'current_simulation_results', None) is None or getattr(self, 'df', None) is None:
            messagebox.showwarning("No data", "Run baseline and proposed simulations to enable series selection.")
            return
        self.update_comparison_plots(self.current_simulation_results, self.df)

    def export_results(self):
        if hasattr(self, 'df') and hasattr(self, 'current_simulation_results'):
            file_path = filedialog.asksaveasfilename(
                defaultextension=".xlsx",
                filetypes=[("Excel files", "*.xlsx"), ("CSV files", "*.csv")]
            )
            if file_path:
                # Ensure we have a summary table ready (fallback to empty if needed)
                try:
                    if not hasattr(self, 'cbo_summary_table') or self.cbo_summary_table is None:
                        _, self.cbo_summary_table = calculate_cbo_summary(
                            self.current_simulation_results,
                            self.df
                        )
                except Exception:
                    self.cbo_summary_table = None

                if file_path.endswith('.xlsx'):
                    with pd.ExcelWriter(file_path) as writer:
                        self.current_simulation_results.to_excel(writer, sheet_name='Current Policy', index=False)
                        self.df.to_excel(writer, sheet_name='Proposed Policy', index=False)
                        # Add CBO-style summary as a third sheet if available
                        if getattr(self, 'cbo_summary_table', None) is not None and not self.cbo_summary_table.empty:
                            self.cbo_summary_table.to_excel(writer, sheet_name='CBO Summary', index=False)
                else:
                    # For CSV, prepend a simple summary section (if available), then append data
                    if getattr(self, 'cbo_summary_table', None) is not None and not self.cbo_summary_table.empty:
                        with open(file_path, 'w', newline='') as f:
                            f.write('CBO-Style Summary\n')
                            self.cbo_summary_table.to_csv(f, index=False)
                            f.write('\n')
                            f.write('Simulation Results\n')
                            combined = pd.concat([
                                self.current_simulation_results.assign(Policy='Current'),
                                self.df.assign(Policy='Proposed')
                            ])
                            combined.to_csv(f, index=False)
                    else:
                        pd.concat([
                            self.current_simulation_results.assign(Policy='Current'),
                            self.df.assign(Policy='Proposed')
                        ]).to_csv(file_path, index=False)
                messagebox.showinfo("Success", "Results exported successfully!")

    def export_current_to_csv(self):
        """Export current policy configuration to a single CSV file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Save Current Policy Configuration"
            )
            if not file_path:
                return

            # Get current values
            current_values = self.collect_current_values()

            # Write to file with proper section formatting
            with open(file_path, 'w', newline='') as f:
                # General Parameters section
                f.write("[General Parameters]\n")
                general_df = pd.DataFrame(list(current_values['general'].items()), columns=['Parameter', 'Value'])
                general_csv = general_df.to_csv(index=False)
                f.write(general_csv)
                if not general_csv.endswith('\n'):
                    f.write('\n')
                f.write("\n")  # Blank line separator

                # Revenues section
                f.write("[Revenues]\n")
                if current_values['revenues']:
                    revenues_df = pd.DataFrame(current_values['revenues'])
                    revenues_csv = revenues_df.to_csv(index=False)
                    f.write(revenues_csv)
                    if not revenues_csv.endswith('\n'):
                        f.write('\n')
                else:
                    f.write("name,is_percent,value,desc,alloc_health,alloc_states,alloc_federal\n")
                f.write("\n")  # Blank line separator

                # Expenditures section
                f.write("[Expenditures]\n")
                if current_values['outs']:
                    outs = []
                    for out in current_values['outs']:
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

            messagebox.showinfo("Success", "Current policy configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def import_current_from_csv(self):
        """Import current policy configuration from a single CSV file"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv")],
                title="Select Current Policy Configuration CSV"
            )
            if not file_path:
                return

            # Read the entire file
            with open(file_path, 'r') as f:
                content = f.read()

            # Split by section headers
            sections = {}
            current_section = None
            section_lines = []

            for line in content.split('\n'):
                line = line.strip()
                if line.startswith('[') and line.endswith(']'):
                    # Save previous section
                    if current_section and section_lines:
                        # Filter out empty lines but keep the data
                        sections[current_section] = '\n'.join([l for l in section_lines if l.strip()])
                    # Start new section
                    current_section = line.strip('[]')
                    section_lines = []
                elif current_section and line:  # Only add non-empty lines
                    section_lines.append(line)

            # Save last section
            if current_section and section_lines:
                sections[current_section] = '\n'.join([l for l in section_lines if l.strip()])

            # Parse General Parameters
            if 'General Parameters' in sections:
                from io import StringIO
                section_data = sections['General Parameters']
                if section_data.strip():  # Check if there's actual data
                    general_df = pd.read_csv(StringIO(section_data))
                    new_general = dict(zip(general_df['Parameter'], general_df['Value']))

                    # FIX: Add missing parameters with defaults if not present
                    if 'stop_on_debt_explosion' not in new_general:
                        new_general['stop_on_debt_explosion'] = 0
                    if 'debt_drag_factor' not in new_general:
                        new_general['debt_drag_factor'] = 0.0
                else:
                    raise ValueError("Empty [General Parameters] section in CSV")
            else:
                raise ValueError("Missing [General Parameters] section in CSV")

            # Parse Revenues
            if 'Revenues' in sections:
                from io import StringIO
                section_data = sections['Revenues']
                if section_data.strip():
                    revenues_df = pd.read_csv(StringIO(section_data))
                    new_revenues = []
                    for _, row in revenues_df.iterrows():
                        # FIX: Properly convert is_percent string to boolean
                        is_percent_val = row.get('is_percent', False)
                        if isinstance(is_percent_val, str):
                            is_percent_val = is_percent_val.lower() in ['true', '1', 'yes']
                        else:
                            is_percent_val = bool(is_percent_val)

                        rev = {
                            'name': row.get('name', ''),
                            'is_percent': is_percent_val,
                            'value': float(row.get('value', 0)),
                            'desc': row.get('desc', ''),
                            'alloc_health': float(row.get('alloc_health', 0)),
                            'alloc_states': float(row.get('alloc_states', 0)),
                            'alloc_federal': float(row.get('alloc_federal', 0))
                        }
                        new_revenues.append(rev)
                else:
                    new_revenues = []
            else:
                raise ValueError("Missing [Revenues] section in CSV")

            # Parse Expenditures
            if 'Expenditures' in sections:
                from io import StringIO
                section_data = sections['Expenditures']
                if section_data.strip():
                    outs_df = pd.read_csv(StringIO(section_data))
                    new_outs = []
                    for _, row in outs_df.iterrows():
                        # FIX: Properly convert is_percent string to boolean
                        is_percent_val = row.get('is_percent', False)
                        if isinstance(is_percent_val, str):
                            is_percent_val = is_percent_val.lower() in ['true', '1', 'yes']
                        else:
                            is_percent_val = bool(is_percent_val)

                        # Get base out data
                        out = {
                            'name': row.get('name', ''),
                            'is_percent': is_percent_val,
                            'value': float(row.get('value', 0))
                        }
                        # Extract allocations
                        allocations = []
                        i = 1
                        while f'alloc_{i}_source' in row.index and f'alloc_{i}_percent' in row.index:
                            src = row.get(f'alloc_{i}_source')
                            pct = row.get(f'alloc_{i}_percent')
                            if pd.notna(src) and src != '':
                                try:
                                    allocations.append({
                                        'source': src,
                                        'percent': float(pct)
                                    })
                                except Exception:
                                    allocations.append({'source': src, 'percent': 0.0})
                            i += 1
                        out['allocations'] = allocations
                        new_outs.append(out)
                else:
                    new_outs = []
            else:
                raise ValueError("Missing [Expenditures] section in CSV")

            # Handle surplus_redirect_target - accept 0.0 or numeric as "no specific target"
            # The simulation will handle this by distributing evenly (with a warning)
            if 'surplus_redirect_target' not in new_general:
                # If missing, add it as 0.0 (no specific target)
                new_general['surplus_redirect_target'] = '0.0'

            # Update current policy with imported values
            self.current_policy = {
                'general': new_general,
                'revenues': new_revenues,
                'outs': new_outs
            }

            # FIX: Refresh the general parameters UI to show new/updated parameters
            # Clear existing general parameter entries
            for widget in self.current_general_entries.values():
                try:
                    widget.master.destroy()  # Destroy the container frame
                except Exception:
                    pass

            self.current_general_entries = {}

            # Recreate general parameter entries
            gen_frame = None
            for child in self.current_general_tab.winfo_children():
                if isinstance(child, ttk.LabelFrame) and "General Parameters" in child.cget('text'):
                    gen_frame = child
                    break

            if gen_frame:
                param_row = 0
                for key, val in self.current_policy['general'].items():
                    container = ttk.Frame(gen_frame)
                    container.grid(row=param_row, column=0, sticky="ew", padx=5, pady=2)
                    container.columnconfigure(1, weight=1)

                    label = ttk.Label(container, text=key.replace('_', ' ').title() + ":")
                    label.grid(row=0, column=0, sticky="w")
                    entry = ttk.Entry(container)
                    entry.insert(0, str(val))
                    entry.grid(row=0, column=1, sticky="ew")
                    self.current_general_entries[key] = entry
                    param_row += 1

            # Refresh the revenues and outs UI
            self.populate_current_policy_data()
            self.run_baseline_simulation()
            messagebox.showinfo("Success", f"Current policy imported from {os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {str(e)}")

    def export_proposed_to_csv(self):
        """Export proposed policy configuration to a single CSV file"""
        try:
            file_path = filedialog.asksaveasfilename(
                defaultextension=".csv",
                filetypes=[("CSV files", "*.csv")],
                title="Save Proposed Policy Configuration"
            )
            if not file_path:
                return

            # Collect proposed values
            proposed_values = self.collect_proposed_values()

            # Write to file with proper section formatting
            with open(file_path, 'w', newline='') as f:
                # General Parameters section
                f.write("[General Parameters]\n")
                general_df = pd.DataFrame(list(proposed_values['general'].items()), columns=['Parameter', 'Value'])
                general_csv = general_df.to_csv(index=False)
                f.write(general_csv)
                if not general_csv.endswith('\n'):
                    f.write('\n')
                f.write("\n")  # Blank line separator

                # Revenues section
                f.write("[Revenues]\n")
                if proposed_values['revenues']:
                    revenues_df = pd.DataFrame(proposed_values['revenues'])
                    revenues_csv = revenues_df.to_csv(index=False)
                    f.write(revenues_csv)
                    if not revenues_csv.endswith('\n'):
                        f.write('\n')
                else:
                    f.write("name,is_percent,value,desc,alloc_health,alloc_states,alloc_federal\n")
                f.write("\n")  # Blank line separator

                # Expenditures section
                f.write("[Expenditures]\n")
                if proposed_values['outs']:
                    outs = []
                    for out in proposed_values['outs']:
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

            messagebox.showinfo("Success", "Proposed policy configuration saved successfully!")
        except Exception as e:
            messagebox.showerror("Export Error", f"Failed to export: {str(e)}")

    def import_proposed_from_csv(self):
        """Import proposed policy configuration from a single CSV file"""
        try:
            file_path = filedialog.askopenfilename(
                filetypes=[("CSV files", "*.csv")],
                title="Select Proposed Policy Configuration CSV"
            )
            if not file_path:
                return

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

            # Parse General Parameters
            if 'General Parameters' not in sections:
                raise ValueError("Missing 'General Parameters' section in CSV")

            general_df = pd.read_csv(io.StringIO(sections['General Parameters']))
            new_general = dict(zip(general_df['Parameter'], general_df['Value']))

            # Update general entries
            for key, value in new_general.items():
                if key in self.general_entries:
                    self.general_entries[key].delete(0, tk.END)
                    self.general_entries[key].insert(0, str(value))

            # Parse Revenues
            new_revenues = []
            if 'Revenues' in sections and sections['Revenues'].strip():
                revenues_df = pd.read_csv(io.StringIO(sections['Revenues']))
                new_revenues = revenues_df.to_dict('records')

            # Clear and repopulate revenues
            self.clear_proposed_ui()
            for rev in new_revenues:
                self.add_revenue(initial=rev)

            # Parse Expenditures
            new_outs = []
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
                    new_outs.append(out)

            # Repopulate outs
            for out in new_outs:
                self.add_out(initial=out)

            messagebox.showinfo("Success", f"Proposed policy imported from {os.path.basename(file_path)}")

        except Exception as e:
            messagebox.showerror("Import Error", f"Failed to import: {str(e)}")

    def collect_proposed_values(self):
        """
        Collect all proposed policy values from the UI with comprehensive validation.

        P0 FIX: Validates empty names/values to prevent simulation crashes.
        """
        # Collect general parameters
        general = {}
        for key, entry in self.general_entries.items():
            # Handle surplus_redirect_target as string, others as float
            if key == 'surplus_redirect_target':
                general[key] = entry.get()
            else:
                try:
                    value_str = entry.get().strip()
                    if not value_str:
                        raise ValueError(f"General parameter '{key}' cannot be empty")
                    general[key] = float(value_str)
                except ValueError as e:
                    raise ValueError(f"Invalid value for general parameter '{key}': {entry.get()} - {str(e)}")

        # Collect revenues with validation
        revenues = []
        for i, d in enumerate(self.revenue_list):
            name = d['name_entry'].get().strip()
            if not name:
                raise ValueError(f"Revenue #{i+1} has an empty name")

            try:
                value_str = d['value_entry'].get().strip()
                if not value_str:
                    raise ValueError(f"Revenue '{name}' has an empty value")
                value = float(value_str)
            except ValueError as e:
                raise ValueError(f"Invalid value for revenue '{name}': {d['value_entry'].get()} - {str(e)}")

            rev = {
                'name': name,
                'is_percent': d['type_var'].get() == '%',
                'value': value,
                'desc': d['desc_entry'].get(),
                'alloc_health': float(d['alloc_health_entry'].get() or 0),
                'alloc_states': float(d['alloc_states_entry'].get() or 0),
                'alloc_federal': float(d['alloc_federal_entry'].get() or 0),
            }
            revenues.append(rev)

        # Collect outs with validation
        outs = []
        for i, d in enumerate(self.out_list):
            name = d['name_entry'].get().strip()
            if not name:
                raise ValueError(f"Out category #{i+1} has an empty name")

            try:
                value_str = d['value_entry'].get().strip()
                if not value_str:
                    raise ValueError(f"Out category '{name}' has an empty value")
                value = float(value_str)
            except ValueError as e:
                raise ValueError(f"Invalid value for out category '{name}': {d['value_entry'].get()} - {str(e)}")

            allocations = []
            for a in d['alloc_list']:
                source = a['combo'].get().strip()
                if not source:
                    raise ValueError(f"Out category '{name}' has an allocation with empty source")
                allocations.append({
                    'source': source,
                    'percent': float(a['percent_entry'].get() or 0)
                })
            out = {
                'name': name,
                'is_percent': d['type_var'].get() == '%',
                'value': value,
                'allocations': allocations
            }
            outs.append(out)

        return {'general': general, 'revenues': revenues, 'outs': outs}

    def show_flow_preview(self, use_current=False):
        """Show a preview of money flow based on current inputs"""
        try:
            # Create a top-level window for the preview
            preview_window = tk.Toplevel(self.root)
            preview_window.title("Money Flow Preview")
            preview_window.geometry("800x600")

            # Create text widget to display the flow
            text = scrolledtext.ScrolledText(preview_window, wrap=tk.WORD, width=80, height=30)
            text.pack(expand=True, fill='both', padx=10, pady=10)
            text.tag_configure('header', font=('TkDefaultFont', 10, 'bold'))
            text.tag_configure('subheader', font=('TkDefaultFont', 9, 'bold'))
            text.tag_configure('normal', font=('TkDefaultFont', 9))

            # Get current values
            if use_current:
                values = self.collect_current_values()
            else:
                values = self.collect_proposed_values()

            # Display General Parameters
            text.insert(tk.END, "General Parameters:\n", 'header')
            text.insert(tk.END, "-" * 50 + "\n", 'normal')
            for param, value in values['general'].items():
                text.insert(tk.END, f"{param.replace('_', ' ').title()}: {value}\n", 'normal')
            text.insert(tk.END, "\n")

            # Display Revenues
            text.insert(tk.END, "Revenue Sources:\n", 'header')
            text.insert(tk.END, "-" * 50 + "\n", 'normal')
            total_health = 0
            total_states = 0
            total_federal = 0

            for rev in values['revenues']:
                text.insert(tk.END, f"\n{rev['name']}\n", 'subheader')
                text.insert(tk.END, f"Type: {'Percentage' if rev['is_percent'] else 'Fixed Amount'}\n", 'normal')
                text.insert(tk.END, f"Value: {rev['value']}\n", 'normal')
                if rev['desc']:
                    text.insert(tk.END, f"Description: {rev['desc']}\n", 'normal')
                text.insert(tk.END, "Allocations:\n", 'normal')
                text.insert(tk.END, f"  Healthcare: {rev['alloc_health']}%\n", 'normal')
                text.insert(tk.END, f"  States: {rev['alloc_states']}%\n", 'normal')
                text.insert(tk.END, f"  Federal: {rev['alloc_federal']}%\n", 'normal')

                total_health += rev['alloc_health']
                total_states += rev['alloc_states']
                total_federal += rev['alloc_federal']

            text.insert(tk.END, "\nTotal Allocations:\n", 'subheader')
            text.insert(tk.END, f"Healthcare: {total_health:.1f}%\n", 'normal')
            text.insert(tk.END, f"States: {total_states:.1f}%\n", 'normal')
            text.insert(tk.END, f"Federal: {total_federal:.1f}%\n", 'normal')
            text.insert(tk.END, "\n")

            # Display Expenditures
            text.insert(tk.END, "Expenditure Categories:\n", 'header')
            text.insert(tk.END, "-" * 50 + "\n", 'normal')
            for out in values['outs']:
                text.insert(tk.END, f"\n{out['name']}\n", 'subheader')
                text.insert(tk.END, f"Type: {'Percentage' if out.get('is_percent', False) else 'Fixed Amount'}\n", 'normal')
                text.insert(tk.END, f"Target: {out['value']}\n", 'normal')
                # Outs don't have 'desc' field, only revenues do
                if 'allocations' in out and out['allocations']:
                    text.insert(tk.END, "Funding Sources:\n", 'normal')
                    for alloc in out['allocations']:
                        text.insert(tk.END, f"  {alloc['source']}: {alloc['percent']}%\n", 'normal')

            # Make text widget read-only
            text.configure(state='disabled')

        except Exception as e:
            messagebox.showerror("Preview Error", f"Failed to generate preview: {str(e)}")
            if 'preview_window' in locals():
                preview_window.destroy()

if __name__ == "__main__":
    root = tk.Tk()
    app = EconomicProjectorApp(root)
    root.mainloop()