"""
GUI for UP2 Generator — converts .MRC files to .UP2 using FrameProcessor.exe.
"""

# GUI template modelled from James Lamb GND GUI: https://github.com/PollockGroup/TriBeam_GND

import os
import subprocess
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk


class UP2GeneratorGui:
    """Main GUI application for UP2 Generator."""

    EXE_PATH = r"C:\direction_electron\Research\Frameprocessor.exe"

    # ── Option maps ──────────────────────────────────────────────────────────
    CAMERA_OPTIONS = {
        "DE12 (0)": 0,
        "DirectView (1)": 1,
        "DE20 (2)": 2,
        "DE16 (3)": 3,
        "DE64 (4)": 4,
        "DESEMCam (5)": 5,
        "LV16 (6)": 6,
        "Vision (7)": 7,
        "Celeritas (8)": 8,
        "Apollo (9)": 9,
        "Survey (10)": 10,
    }
    FRAME_TOPOLOGY_OPTIONS = {"Single (0)": 0, "Top/Bottom (1)": 1, "Left/Right (2)": 2}
    ACQUISITION_TYPE_OPTIONS = {"Data (0)": 0, "Dark Reference (1)": 1, "Gain Reference (2)": 2}
    THRESHOLDING_TYPE_OPTIONS = {
        "Disabled (0)": 0,
        "Low to Zero (1)": 1,
        "Adaptive to Zero (2)": 2,
        "Adaptive Subtraction (3)": 3,
    }
    ADAPTIVE_THRESHOLDING_OPTIONS = {"Mean (0)": 0, "Median (1)": 1, "Quartile (2)": 2}
    COUNTING_OPTIONS = {
        "Disabled (0)": 0,
        "Maxima (1)": 1,
        "Centroid (2)": 2,
        "Binary Centroid (3)": 3,
        "HDR Maxima (4)": 4,
        "HDR Centroid (5)": 5,
        "HDR Binary Centroid (6)": 6,
        "DEEP (7)": 7,
        "HDR DEEP (8)": 8,
        "EER (9)": 9,
    }
    BINNING_METHOD_OPTIONS = {
        "Sample (0)": 0,
        "Sum (1)": 1,
        "Average (2)": 2,
        "Fourier Crop (3)": 3,
    }
    ROTATION_OPTIONS = {"None": None, "Counterclockwise (-1)": -1, "Clockwise (1)": 1}
    OKRA_OPTIONS = {"Default (-1)": -1, "Disable (0)": 0, "Enable (1)": 1}
    MOVIE_BITRATE_OPTIONS = {
        "8-bit unsigned integer": 8,
        "16-bit unsigned integer (default)": 16,
        "32-bit floating point": 32,
    }
    TOTAL_BITRATE_OPTIONS = {
        "8-bit unsigned integer": 8,
        "16-bit unsigned integer": 16,
        "32-bit floating point (default)": 32,
    }
    VIRTUAL_IMAGE_METHODS = {
        "Sum (1)": 1,
        "Centroid Amplitude (2)": 2,
        "Centroid Angle (3)": 3,
        "Centroid X (4)": 4,
        "Centroid Y (5)": 5,
    }

    def __init__(self, root):
        self.root = root
        self.root.title("UP2 Generator")
        self.root.geometry("750x900")
        self.root.resizable(True, True)

        # ── Main settings variables ──────────────────────────────────────────
        self.mrc_file_path = tk.StringVar()
        self.camera = tk.StringVar(value="Celeritas (8)")
        self.moviesumframes = tk.StringVar(value="1")
        self.singlethread = tk.BooleanVar(value=True)
        self.fliphorizontal = tk.BooleanVar(value=True)
        self.flipvertical = tk.BooleanVar(value=True)
        self.gainreference = tk.StringVar(value="none")
        self.binning = tk.StringVar(value="2")
        self.scanning_x = tk.StringVar(value="392")
        self.scanning_y = tk.StringVar(value="392")

        # ── Advanced: Input Options ──────────────────────────────────────────
        self.adv_first_enabled = tk.BooleanVar(value=False)
        self.adv_first = tk.StringVar(value="0")
        self.adv_last_enabled = tk.BooleanVar(value=False)
        self.adv_last = tk.StringVar(value="0")
        self.adv_frametopology_enabled = tk.BooleanVar(value=False)
        self.adv_frametopology = tk.StringVar(value="Single (0)")
        self.adv_framesperbuffer_enabled = tk.BooleanVar(value=False)
        self.adv_framesperbuffer = tk.StringVar(value="1")
        self.adv_hardwarebinning = tk.BooleanVar(value=False)
        self.adv_hardwareroioffset_enabled = tk.BooleanVar(value=False)
        self.adv_hardwareroioffset_x = tk.StringVar(value="0")
        self.adv_hardwareroioffset_y = tk.StringVar(value="0")
        self.adv_globalshutter = tk.BooleanVar(value=False)
        self.adv_offchipcds = tk.BooleanVar(value=False)
        self.adv_hdrlevels_enabled = tk.BooleanVar(value=False)
        self.adv_hdrlevels = tk.StringVar(value="1")
        self.adv_okra_enabled = tk.BooleanVar(value=False)
        self.adv_okra = tk.StringVar(value="Default (-1)")
        self.adv_metadataxml_enabled = tk.BooleanVar(value=False)
        self.adv_metadataxml = tk.StringVar(value="")

        # ── Advanced: Acquisition Options ───────────────────────────────────
        self.adv_acquisitiontype_enabled = tk.BooleanVar(value=False)
        self.adv_acquisitiontype = tk.StringVar(value="Data (0)")
        self.adv_aduperevent_enabled = tk.BooleanVar(value=False)
        self.adv_aduperevent = tk.StringVar(value="1.0")

        # ── Advanced: Thresholding Options ──────────────────────────────────
        self.adv_thresholdingtype_enabled = tk.BooleanVar(value=False)
        self.adv_thresholdingtype = tk.StringVar(value="Disabled (0)")
        self.adv_adaptivethresholding_enabled = tk.BooleanVar(value=False)
        self.adv_adaptivethresholding = tk.StringVar(value="Mean (0)")
        self.adv_threshold_enabled = tk.BooleanVar(value=False)
        self.adv_threshold = tk.StringVar(value="0.0")

        # ── Advanced: HDR Options ────────────────────────────────────────────
        self.adv_thresholdhdr1_enabled = tk.BooleanVar(value=False)
        self.adv_thresholdhdr1 = tk.StringVar(value="0.0")
        self.adv_thresholdhdr2_enabled = tk.BooleanVar(value=False)
        self.adv_thresholdhdr2 = tk.StringVar(value="0.0")
        self.adv_hdrmergemin0_enabled = tk.BooleanVar(value=False)
        self.adv_hdrmergemin0 = tk.StringVar(value="0.0")
        self.adv_hdrmergemax0_enabled = tk.BooleanVar(value=False)
        self.adv_hdrmergemax0 = tk.StringVar(value="0.0")
        self.adv_hdrmergemin1_enabled = tk.BooleanVar(value=False)
        self.adv_hdrmergemin1 = tk.StringVar(value="0.0")
        self.adv_hdrmergemax1_enabled = tk.BooleanVar(value=False)
        self.adv_hdrmergemax1 = tk.StringVar(value="0.0")
        self.adv_hdrgainfactor1_enabled = tk.BooleanVar(value=False)
        self.adv_hdrgainfactor1 = tk.StringVar(value="1.0")
        self.adv_hdrgainfactor2_enabled = tk.BooleanVar(value=False)
        self.adv_hdrgainfactor2 = tk.StringVar(value="1.0")

        # ── Advanced: Event Counting Options ────────────────────────────────
        self.adv_counting_enabled = tk.BooleanVar(value=False)
        self.adv_counting = tk.StringVar(value="Disabled (0)")
        self.adv_eventthresholdmin_enabled = tk.BooleanVar(value=False)
        self.adv_eventthresholdmin = tk.StringVar(value="0.0")
        self.adv_eventthresholdmax_enabled = tk.BooleanVar(value=False)
        self.adv_eventthresholdmax = tk.StringVar(value="0.0")

        # ── Advanced: Processing Options ────────────────────────────────────
        self.adv_processframesperbuffer_enabled = tk.BooleanVar(value=False)
        self.adv_processframesperbuffer = tk.StringVar(value="1")
        self.adv_processoutputbuffersize_enabled = tk.BooleanVar(value=False)
        self.adv_processoutputbuffersize = tk.StringVar(value="8")
        self.adv_simulateinput = tk.BooleanVar(value=False)

        # ── Advanced: Dark Reference Options ────────────────────────────────
        self.adv_darkreference_enabled = tk.BooleanVar(value=False)
        self.adv_darkreference = tk.StringVar(value="")
        self.adv_darkreferencehdr1_enabled = tk.BooleanVar(value=False)
        self.adv_darkreferencehdr1 = tk.StringVar(value="")
        self.adv_darkreferencehdr2_enabled = tk.BooleanVar(value=False)
        self.adv_darkreferencehdr2 = tk.StringVar(value="")
        self.adv_darkreferenceoffchipcds_enabled = tk.BooleanVar(value=False)
        self.adv_darkreferenceoffchipcds = tk.StringVar(value="")

        # ── Advanced: Gain Reference Options ────────────────────────────────
        self.adv_gainreferencehdr1_enabled = tk.BooleanVar(value=False)
        self.adv_gainreferencehdr1 = tk.StringVar(value="")
        self.adv_gainreferencehdr2_enabled = tk.BooleanVar(value=False)
        self.adv_gainreferencehdr2 = tk.StringVar(value="")
        self.adv_gainreferencecounting_enabled = tk.BooleanVar(value=False)
        self.adv_gainreferencecounting = tk.StringVar(value="")

        # ── Advanced: Bad Pixel Options ─────────────────────────────────────
        self.adv_badpixelsxml_enabled = tk.BooleanVar(value=False)
        self.adv_badpixelsxml = tk.StringVar(value="")
        self.adv_badpixelsoutput = tk.BooleanVar(value=False)

        # ── Advanced: Output Options ─────────────────────────────────────────
        self.adv_binningmethod_enabled = tk.BooleanVar(value=False)
        self.adv_binningmethod = tk.StringVar(value="Sum (1)")
        self.adv_rotation_enabled = tk.BooleanVar(value=False)
        self.adv_rotation = tk.StringVar(value="None")
        self.adv_roi_enabled = tk.BooleanVar(value=False)
        self.adv_roi_xoffset = tk.StringVar(value="0")
        self.adv_roi_yoffset = tk.StringVar(value="0")
        self.adv_roi_xsize = tk.StringVar(value="0")
        self.adv_roi_ysize = tk.StringVar(value="0")
        self.adv_multiply_enabled = tk.BooleanVar(value=False)
        self.adv_multiply = tk.StringVar(value="1.0")

        # ── Advanced: 4D Scanning Options ───────────────────────────────────
        self.adv_scanningcroptop_enabled = tk.BooleanVar(value=False)
        self.adv_scanningcroptop = tk.StringVar(value="0")
        self.adv_scanningcropbottom_enabled = tk.BooleanVar(value=False)
        self.adv_scanningcropbottom = tk.StringVar(value="0")
        self.adv_scanningcropleft_enabled = tk.BooleanVar(value=False)
        self.adv_scanningcropleft = tk.StringVar(value="0")
        self.adv_scanningcropright_enabled = tk.BooleanVar(value=False)
        self.adv_scanningcropright = tk.StringVar(value="0")
        self.adv_scanningvacuumref_enabled = tk.BooleanVar(value=False)
        self.adv_scanningvacuumref_x = tk.StringVar(value="")
        self.adv_scanningvacuumref_y = tk.StringVar(value="")

        # ── Advanced: Virtual Image Options ─────────────────────────────────
        self.adv_virtualimage0_enabled = tk.BooleanVar(value=False)
        self.adv_virtualimage0_method = tk.StringVar(value="Sum (1)")
        for i in range(1, 5):
            setattr(self, f"adv_virtualimage{i}_enabled", tk.BooleanVar(value=False))
            setattr(self, f"adv_virtualimage{i}_mask", tk.StringVar(value=""))
            setattr(self, f"adv_virtualimage{i}_method", tk.StringVar(value="Sum (1)"))

        # ── Advanced: File Output Options ────────────────────────────────────
        self.adv_outputtiff = tk.BooleanVar(value=False)
        self.adv_outputlzw = tk.BooleanVar(value=False)
        self.adv_outputde5 = tk.BooleanVar(value=False)
        self.adv_moviebitrate_enabled = tk.BooleanVar(value=False)
        self.adv_moviebitrate = tk.StringVar(value="16-bit unsigned integer (default)")
        self.adv_movieuncorrected = tk.BooleanVar(value=False)
        self.adv_totalintegrated = tk.BooleanVar(value=False)
        self.adv_totalcounted = tk.BooleanVar(value=False)
        self.adv_totalbitrate_enabled = tk.BooleanVar(value=False)
        self.adv_totalbitrate = tk.StringVar(value="32-bit floating point (default)")
        self.adv_intensityhistogram_enabled = tk.BooleanVar(value=False)
        self.adv_intensityhistogram_min = tk.StringVar(value="0.0")
        self.adv_intensityhistogram_max = tk.StringVar(value="1.0")
        self.adv_intensityhistogram_count = tk.StringVar(value="100")
        self.adv_intensityhistogramroi_enabled = tk.BooleanVar(value=False)
        self.adv_intensityhistogramroi_xo = tk.StringVar(value="0")
        self.adv_intensityhistogramroi_yo = tk.StringVar(value="0")
        self.adv_intensityhistogramroi_xs = tk.StringVar(value="0")
        self.adv_intensityhistogramroi_ys = tk.StringVar(value="0")

        # ── Advanced: Misc ───────────────────────────────────────────────────
        self.adv_quiet = tk.BooleanVar(value=False)
        self.adv_silent = tk.BooleanVar(value=False)

        self._create_widgets()

        # Trace all tk variables to keep command preview live
        for attr_name in list(vars(self)):
            attr = getattr(self, attr_name)
            if isinstance(attr, (tk.StringVar, tk.BooleanVar)):
                attr.trace_add("write", lambda *_: self._update_command_preview())

        self._update_command_preview()

    # ── Widget construction ──────────────────────────────────────────────────

    def _create_widgets(self):
        """Create all top-level GUI widgets."""
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="nsew")
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=3)
        main_frame.rowconfigure(4, weight=1)

        row = 0

        # EXE path display
        exe_frame = ttk.LabelFrame(main_frame, text="Executable", padding="5")
        exe_frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        exe_frame.columnconfigure(1, weight=1)
        ttk.Label(exe_frame, text="FrameProcessor.exe:").grid(
            row=0, column=0, sticky="w", padx=(0, 8)
        )
        ttk.Label(exe_frame, text=self.EXE_PATH, foreground="gray").grid(
            row=0, column=1, sticky="w"
        )
        row += 1

        # Notebook (Main / Advanced)
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.grid(row=row, column=0, sticky="nsew", pady=(0, 5))
        row += 1

        main_tab = ttk.Frame(self.notebook, padding="10")
        self.notebook.add(main_tab, text="Main Settings")
        main_tab.columnconfigure(1, weight=1)
        self._create_main_tab(main_tab)

        adv_outer = ttk.Frame(self.notebook)
        self.notebook.add(adv_outer, text="Advanced Settings")
        self._create_advanced_tab(adv_outer)

        # Command preview
        cmd_frame = ttk.LabelFrame(main_frame, text="Command Preview", padding="5")
        cmd_frame.grid(row=row, column=0, sticky="ew", pady=(0, 5))
        cmd_frame.columnconfigure(0, weight=1)
        row += 1

        self.cmd_text = tk.Text(
            cmd_frame, height=3, wrap="word", state="disabled", background="#f0f0f0"
        )
        self.cmd_text.grid(row=0, column=0, sticky="ew")
        cmd_scroll = ttk.Scrollbar(cmd_frame, orient="vertical", command=self.cmd_text.yview)
        cmd_scroll.grid(row=0, column=1, sticky="ns")
        self.cmd_text.config(yscrollcommand=cmd_scroll.set)

        # Buttons
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=row, column=0, pady=5)
        row += 1

        self.run_button = ttk.Button(button_frame, text="Run", command=self._run)
        self.run_button.pack(side="left", padx=5)
        ttk.Button(button_frame, text="Copy Command", command=self._copy_command).pack(
            side="left", padx=5
        )

        # Log output
        log_frame = ttk.LabelFrame(main_frame, text="Output Log", padding="5")
        log_frame.grid(row=row, column=0, sticky="nsew", pady=(0, 5))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)

        self.log_text = tk.Text(log_frame, height=6, state="disabled")
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll = ttk.Scrollbar(log_frame, orient="vertical", command=self.log_text.yview)
        log_scroll.grid(row=0, column=1, sticky="ns")
        self.log_text.config(yscrollcommand=log_scroll.set)

    def _create_main_tab(self, parent):
        """Widgets for the Main Settings tab."""
        row = 0

        # Input MRC file
        ttk.Label(parent, text="Input MRC File:", font=("", 10, "bold")).grid(
            row=row, column=0, sticky="w", pady=2
        )
        file_frame = ttk.Frame(parent)
        file_frame.grid(row=row, column=1, sticky="ew", pady=2)
        file_frame.columnconfigure(0, weight=1)
        ttk.Entry(file_frame, textvariable=self.mrc_file_path).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(file_frame, text="Browse...", command=self._browse_mrc).grid(row=0, column=1)
        row += 1

        ttk.Separator(parent, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # Camera
        ttk.Label(parent, text="Camera:").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Combobox(
            parent,
            textvariable=self.camera,
            values=list(self.CAMERA_OPTIONS.keys()),
            state="readonly",
            width=25,
        ).grid(row=row, column=1, sticky="w", pady=2)
        row += 1

        # Movie sum frames
        ttk.Label(parent, text="Movie Sum Frames:").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Spinbox(parent, textvariable=self.moviesumframes, from_=1, to=9999, width=8).grid(
            row=row, column=1, sticky="w", pady=2
        )
        row += 1

        # Single thread
        ttk.Label(parent, text="Single Thread:").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, variable=self.singlethread).grid(
            row=row, column=1, sticky="w", pady=2
        )
        row += 1

        # Flip horizontal
        ttk.Label(parent, text="Flip Horizontal:").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, variable=self.fliphorizontal).grid(
            row=row, column=1, sticky="w", pady=2
        )
        row += 1

        # Flip vertical
        ttk.Label(parent, text="Flip Vertical:").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Checkbutton(parent, variable=self.flipvertical).grid(
            row=row, column=1, sticky="w", pady=2
        )
        row += 1

        ttk.Separator(parent, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # Gain reference
        ttk.Label(parent, text="Gain Reference:").grid(row=row, column=0, sticky="w", pady=2)
        gr_frame = ttk.Frame(parent)
        gr_frame.grid(row=row, column=1, sticky="ew", pady=2)
        gr_frame.columnconfigure(0, weight=1)
        ttk.Entry(gr_frame, textvariable=self.gainreference).grid(
            row=0, column=0, sticky="ew", padx=(0, 5)
        )
        ttk.Button(gr_frame, text="Browse...", command=self._browse_gainref).grid(row=0, column=1)
        ttk.Button(
            gr_frame, text="None", command=lambda: self.gainreference.set("none")
        ).grid(row=0, column=2, padx=(3, 0))
        row += 1

        ttk.Separator(parent, orient="horizontal").grid(
            row=row, column=0, columnspan=2, sticky="ew", pady=8
        )
        row += 1

        # Binning
        ttk.Label(parent, text="Binning:").grid(row=row, column=0, sticky="w", pady=2)
        ttk.Spinbox(parent, textvariable=self.binning, from_=1, to=16, width=8).grid(
            row=row, column=1, sticky="w", pady=2
        )
        row += 1

        # Scanning dimensions
        ttk.Label(parent, text="Scanning (X  Y):").grid(row=row, column=0, sticky="w", pady=2)
        scan_frame = ttk.Frame(parent)
        scan_frame.grid(row=row, column=1, sticky="w", pady=2)
        ttk.Spinbox(scan_frame, textvariable=self.scanning_x, from_=1, to=99999, width=8).pack(
            side="left", padx=(0, 5)
        )
        ttk.Spinbox(scan_frame, textvariable=self.scanning_y, from_=1, to=99999, width=8).pack(
            side="left"
        )

    def _create_advanced_tab(self, parent):
        """Create the scrollable Advanced Settings tab."""
        canvas = tk.Canvas(parent)
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=canvas.yview)
        canvas.configure(yscrollcommand=scrollbar.set)

        scrollbar.pack(side="right", fill="y")
        canvas.pack(side="left", fill="both", expand=True)

        adv_frame = ttk.Frame(canvas, padding="10")
        canvas_window = canvas.create_window((0, 0), window=adv_frame, anchor="nw")

        def _on_frame_configure(event):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def _on_canvas_configure(event):
            canvas.itemconfig(canvas_window, width=event.width)

        def _on_mousewheel(event):
            canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

        adv_frame.bind("<Configure>", _on_frame_configure)
        canvas.bind("<Configure>", _on_canvas_configure)
        canvas.bind("<Enter>", lambda e: canvas.bind_all("<MouseWheel>", _on_mousewheel))
        canvas.bind("<Leave>", lambda e: canvas.unbind_all("<MouseWheel>"))

        adv_frame.columnconfigure(2, weight=1)

        row = 0

        # ── Helper closures ──────────────────────────────────────────────────
        def sep():
            nonlocal row
            ttk.Separator(adv_frame, orient="horizontal").grid(
                row=row, column=0, columnspan=3, sticky="ew", pady=6
            )
            row += 1

        def section(text):
            nonlocal row
            ttk.Label(adv_frame, text=text, font=("", 10, "bold")).grid(
                row=row, column=0, columnspan=3, sticky="w", pady=(4, 2)
            )
            row += 1

        def flag_row(label, enabled_var, make_widget):
            """Checkbox | label | widget row for optional flags."""
            nonlocal row
            ttk.Checkbutton(adv_frame, variable=enabled_var).grid(
                row=row, column=0, sticky="w", padx=(0, 4)
            )
            ttk.Label(adv_frame, text=label).grid(row=row, column=1, sticky="w", pady=2)
            w = make_widget(adv_frame)
            w.grid(row=row, column=2, sticky="w", pady=2, padx=(5, 0))
            row += 1
            return w

        def bool_row(label, bool_var):
            """Simple full-width boolean flag row."""
            nonlocal row
            ttk.Label(adv_frame, text=label).grid(
                row=row, column=0, columnspan=2, sticky="w", pady=2
            )
            ttk.Checkbutton(adv_frame, variable=bool_var).grid(
                row=row, column=2, sticky="w", pady=2
            )
            row += 1

        def file_flag_row(label, enabled_var, path_var, filetypes):
            """Checkbox | label | Entry + Browse for file-path flags."""
            nonlocal row
            ttk.Checkbutton(adv_frame, variable=enabled_var).grid(
                row=row, column=0, sticky="w", padx=(0, 4)
            )
            ttk.Label(adv_frame, text=label).grid(row=row, column=1, sticky="w", pady=2)
            f = ttk.Frame(adv_frame)
            f.grid(row=row, column=2, sticky="ew", pady=2, padx=(5, 0))
            f.columnconfigure(0, weight=1)
            ttk.Entry(f, textvariable=path_var, width=22).grid(
                row=0, column=0, sticky="ew", padx=(0, 5)
            )
            ttk.Button(
                f,
                text="Browse...",
                command=lambda v=path_var, ft=filetypes: self._browse_any(v, ft),
            ).grid(row=0, column=1)
            row += 1

        # ── Input Options ────────────────────────────────────────────────────
        section("Input Options")
        flag_row(
            "-first",
            self.adv_first_enabled,
            lambda p: ttk.Spinbox(p, textvariable=self.adv_first, from_=-9999, to=9999, width=8),
        )
        flag_row(
            "-last",
            self.adv_last_enabled,
            lambda p: ttk.Spinbox(p, textvariable=self.adv_last, from_=-9999, to=9999, width=8),
        )
        flag_row(
            "-frametopology",
            self.adv_frametopology_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_frametopology,
                values=list(self.FRAME_TOPOLOGY_OPTIONS.keys()),
                state="readonly",
                width=20,
            ),
        )
        flag_row(
            "-framesperbuffer",
            self.adv_framesperbuffer_enabled,
            lambda p: ttk.Spinbox(
                p, textvariable=self.adv_framesperbuffer, from_=1, to=9999, width=8
            ),
        )
        bool_row("-hardwarebinning", self.adv_hardwarebinning)

        # hardwareroioffset (two values)
        ttk.Checkbutton(adv_frame, variable=self.adv_hardwareroioffset_enabled).grid(
            row=row, column=0, sticky="w", padx=(0, 4)
        )
        ttk.Label(adv_frame, text="-hardwareroioffset (X  Y):").grid(
            row=row, column=1, sticky="w", pady=2
        )
        hroi_f = ttk.Frame(adv_frame)
        hroi_f.grid(row=row, column=2, sticky="w", pady=2, padx=(5, 0))
        ttk.Spinbox(hroi_f, textvariable=self.adv_hardwareroioffset_x, from_=0, to=9999, width=8).pack(side="left", padx=(0, 5))
        ttk.Spinbox(hroi_f, textvariable=self.adv_hardwareroioffset_y, from_=0, to=9999, width=8).pack(side="left")
        row += 1

        bool_row("-globalshutter", self.adv_globalshutter)
        bool_row("-offchipcds", self.adv_offchipcds)
        flag_row(
            "-hdrlevels",
            self.adv_hdrlevels_enabled,
            lambda p: ttk.Spinbox(p, textvariable=self.adv_hdrlevels, from_=1, to=10, width=8),
        )
        flag_row(
            "-okra",
            self.adv_okra_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_okra,
                values=list(self.OKRA_OPTIONS.keys()),
                state="readonly",
                width=18,
            ),
        )
        file_flag_row(
            "-metadataxml:",
            self.adv_metadataxml_enabled,
            self.adv_metadataxml,
            [("XML files", "*.xml"), ("All files", "*.*")],
        )

        sep()
        # ── Acquisition Options ──────────────────────────────────────────────
        section("Acquisition Options")
        flag_row(
            "-acquisitiontype",
            self.adv_acquisitiontype_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_acquisitiontype,
                values=list(self.ACQUISITION_TYPE_OPTIONS.keys()),
                state="readonly",
                width=20,
            ),
        )
        flag_row(
            "-aduperevent",
            self.adv_aduperevent_enabled,
            lambda p: ttk.Entry(p, textvariable=self.adv_aduperevent, width=10),
        )

        sep()
        # ── Thresholding Options ─────────────────────────────────────────────
        section("Thresholding Options")
        flag_row(
            "-thresholdingtype",
            self.adv_thresholdingtype_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_thresholdingtype,
                values=list(self.THRESHOLDING_TYPE_OPTIONS.keys()),
                state="readonly",
                width=25,
            ),
        )
        flag_row(
            "-adaptivethresholding",
            self.adv_adaptivethresholding_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_adaptivethresholding,
                values=list(self.ADAPTIVE_THRESHOLDING_OPTIONS.keys()),
                state="readonly",
                width=15,
            ),
        )
        flag_row(
            "-threshold",
            self.adv_threshold_enabled,
            lambda p: ttk.Entry(p, textvariable=self.adv_threshold, width=10),
        )

        sep()
        # ── HDR Options ──────────────────────────────────────────────────────
        section("HDR Options")
        for lbl, en, var in [
            ("-thresholdhdr1", self.adv_thresholdhdr1_enabled, self.adv_thresholdhdr1),
            ("-thresholdhdr2", self.adv_thresholdhdr2_enabled, self.adv_thresholdhdr2),
            ("-hdrmergemin0", self.adv_hdrmergemin0_enabled, self.adv_hdrmergemin0),
            ("-hdrmergemax0", self.adv_hdrmergemax0_enabled, self.adv_hdrmergemax0),
            ("-hdrmergemin1", self.adv_hdrmergemin1_enabled, self.adv_hdrmergemin1),
            ("-hdrmergemax1", self.adv_hdrmergemax1_enabled, self.adv_hdrmergemax1),
            ("-hdrgainfactor1", self.adv_hdrgainfactor1_enabled, self.adv_hdrgainfactor1),
            ("-hdrgainfactor2", self.adv_hdrgainfactor2_enabled, self.adv_hdrgainfactor2),
        ]:
            flag_row(lbl, en, lambda p, v=var: ttk.Entry(p, textvariable=v, width=10))

        sep()
        # ── Event Counting Options ───────────────────────────────────────────
        section("Event Counting Options")
        flag_row(
            "-counting",
            self.adv_counting_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_counting,
                values=list(self.COUNTING_OPTIONS.keys()),
                state="readonly",
                width=25,
            ),
        )
        flag_row(
            "-eventthresholdmin",
            self.adv_eventthresholdmin_enabled,
            lambda p: ttk.Entry(p, textvariable=self.adv_eventthresholdmin, width=10),
        )
        flag_row(
            "-eventthresholdmax",
            self.adv_eventthresholdmax_enabled,
            lambda p: ttk.Entry(p, textvariable=self.adv_eventthresholdmax, width=10),
        )

        sep()
        # ── Processing Options ───────────────────────────────────────────────
        section("Processing Options")
        flag_row(
            "-processframesperbuffer",
            self.adv_processframesperbuffer_enabled,
            lambda p: ttk.Spinbox(
                p, textvariable=self.adv_processframesperbuffer, from_=1, to=9999, width=8
            ),
        )
        flag_row(
            "-processoutputbuffersize",
            self.adv_processoutputbuffersize_enabled,
            lambda p: ttk.Spinbox(
                p, textvariable=self.adv_processoutputbuffersize, from_=1, to=999, width=8
            ),
        )
        bool_row("-simulateinput", self.adv_simulateinput)

        sep()
        # ── Dark Reference Options ───────────────────────────────────────────
        section("Dark Reference Options")
        mrc_tiff_types = [("MRC/TIFF files", "*.mrc *.tif *.tiff"), ("All files", "*.*")]
        for lbl, en, pv in [
            ("-darkreference:", self.adv_darkreference_enabled, self.adv_darkreference),
            ("-darkreferencehdr1:", self.adv_darkreferencehdr1_enabled, self.adv_darkreferencehdr1),
            ("-darkreferencehdr2:", self.adv_darkreferencehdr2_enabled, self.adv_darkreferencehdr2),
            (
                "-darkreferenceoffchipcds:",
                self.adv_darkreferenceoffchipcds_enabled,
                self.adv_darkreferenceoffchipcds,
            ),
        ]:
            file_flag_row(lbl, en, pv, mrc_tiff_types)

        sep()
        # ── Gain Reference Options ───────────────────────────────────────────
        section("Gain Reference Options")
        for lbl, en, pv in [
            ("-gainreferencehdr1:", self.adv_gainreferencehdr1_enabled, self.adv_gainreferencehdr1),
            ("-gainreferencehdr2:", self.adv_gainreferencehdr2_enabled, self.adv_gainreferencehdr2),
            (
                "-gainreferencecounting:",
                self.adv_gainreferencecounting_enabled,
                self.adv_gainreferencecounting,
            ),
        ]:
            file_flag_row(lbl, en, pv, mrc_tiff_types)

        sep()
        # ── Bad Pixel Options ───────────────────────────────────────────────
        section("Bad Pixel Options")
        file_flag_row(
            "-badpixelsxml:",
            self.adv_badpixelsxml_enabled,
            self.adv_badpixelsxml,
            [("XML files", "*.xml"), ("All files", "*.*")],
        )
        bool_row("-badpixelsoutput", self.adv_badpixelsoutput)

        sep()
        # ── Output Options ───────────────────────────────────────────────────
        section("Output Options")
        flag_row(
            "-binningmethod",
            self.adv_binningmethod_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_binningmethod,
                values=list(self.BINNING_METHOD_OPTIONS.keys()),
                state="readonly",
                width=20,
            ),
        )
        flag_row(
            "-rotation",
            self.adv_rotation_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_rotation,
                values=list(self.ROTATION_OPTIONS.keys()),
                state="readonly",
                width=22,
            ),
        )

        # -roi (four values)
        ttk.Checkbutton(adv_frame, variable=self.adv_roi_enabled).grid(
            row=row, column=0, sticky="w", padx=(0, 4)
        )
        ttk.Label(adv_frame, text="-roi (xoff yoff xsize ysize):").grid(
            row=row, column=1, sticky="w", pady=2
        )
        roi_f = ttk.Frame(adv_frame)
        roi_f.grid(row=row, column=2, sticky="w", pady=2, padx=(5, 0))
        for rv in (self.adv_roi_xoffset, self.adv_roi_yoffset, self.adv_roi_xsize, self.adv_roi_ysize):
            ttk.Spinbox(roi_f, textvariable=rv, from_=0, to=99999, width=7).pack(
                side="left", padx=(0, 3)
            )
        row += 1

        flag_row(
            "-multiply",
            self.adv_multiply_enabled,
            lambda p: ttk.Entry(p, textvariable=self.adv_multiply, width=10),
        )

        sep()
        # ── 4D Scanning Options ──────────────────────────────────────────────
        section("4D Scanning Options")
        for lbl, en, sv in [
            ("-scanningcroptop:", self.adv_scanningcroptop_enabled, self.adv_scanningcroptop),
            (
                "-scanningcropbottom:",
                self.adv_scanningcropbottom_enabled,
                self.adv_scanningcropbottom,
            ),
            ("-scanningcropleft:", self.adv_scanningcropleft_enabled, self.adv_scanningcropleft),
            ("-scanningcropright:", self.adv_scanningcropright_enabled, self.adv_scanningcropright),
        ]:
            flag_row(
                lbl, en, lambda p, v=sv: ttk.Spinbox(p, textvariable=v, from_=0, to=9999, width=8)
            )

        # -scanningvacuumref (two file paths)
        ttk.Checkbutton(adv_frame, variable=self.adv_scanningvacuumref_enabled).grid(
            row=row, column=0, sticky="w", padx=(0, 4)
        )
        ttk.Label(adv_frame, text="-scanningvacuumref (X  Y):").grid(
            row=row, column=1, sticky="w", pady=2
        )
        vref_f = ttk.Frame(adv_frame)
        vref_f.grid(row=row, column=2, sticky="ew", pady=2, padx=(5, 0))
        vref_f.columnconfigure(0, weight=1)
        vref_f.columnconfigure(2, weight=1)
        ttk.Entry(vref_f, textvariable=self.adv_scanningvacuumref_x, width=14).grid(
            row=0, column=0, sticky="ew", padx=(0, 3)
        )
        ttk.Button(
            vref_f,
            text="Browse X",
            command=lambda: self._browse_any(
                self.adv_scanningvacuumref_x, [("All files", "*.*")]
            ),
        ).grid(row=0, column=1, padx=(0, 6))
        ttk.Entry(vref_f, textvariable=self.adv_scanningvacuumref_y, width=14).grid(
            row=0, column=2, sticky="ew", padx=(0, 3)
        )
        ttk.Button(
            vref_f,
            text="Browse Y",
            command=lambda: self._browse_any(
                self.adv_scanningvacuumref_y, [("All files", "*.*")]
            ),
        ).grid(row=0, column=3)
        row += 1

        sep()
        # ── Virtual Image Options ─────────────────────────────────────────────
        section("Virtual Image Options")

        # virtualimage0 — method only, no mask
        ttk.Checkbutton(adv_frame, variable=self.adv_virtualimage0_enabled).grid(
            row=row, column=0, sticky="w", padx=(0, 4)
        )
        ttk.Label(adv_frame, text="-virtualimage0 (method):").grid(
            row=row, column=1, sticky="w", pady=2
        )
        ttk.Combobox(
            adv_frame,
            textvariable=self.adv_virtualimage0_method,
            values=list(self.VIRTUAL_IMAGE_METHODS.keys()),
            state="readonly",
            width=25,
        ).grid(row=row, column=2, sticky="w", pady=2, padx=(5, 0))
        row += 1

        # virtualimage1-4 — mask file + method
        for i in range(1, 5):
            en = getattr(self, f"adv_virtualimage{i}_enabled")
            mask_v = getattr(self, f"adv_virtualimage{i}_mask")
            meth_v = getattr(self, f"adv_virtualimage{i}_method")
            ttk.Checkbutton(adv_frame, variable=en).grid(
                row=row, column=0, sticky="w", padx=(0, 4)
            )
            ttk.Label(adv_frame, text=f"-virtualimage{i}:").grid(
                row=row, column=1, sticky="w", pady=2
            )
            vi_f = ttk.Frame(adv_frame)
            vi_f.grid(row=row, column=2, sticky="ew", pady=2, padx=(5, 0))
            vi_f.columnconfigure(0, weight=1)
            ttk.Entry(vi_f, textvariable=mask_v, width=14).grid(
                row=0, column=0, sticky="ew", padx=(0, 3)
            )
            ttk.Button(
                vi_f,
                text="Browse...",
                command=lambda v=mask_v: self._browse_any(v, mrc_tiff_types),
            ).grid(row=0, column=1, padx=(0, 5))
            ttk.Combobox(
                vi_f,
                textvariable=meth_v,
                values=list(self.VIRTUAL_IMAGE_METHODS.keys()),
                state="readonly",
                width=22,
            ).grid(row=0, column=2)
            row += 1

        sep()
        # ── File Output Options ───────────────────────────────────────────────
        section("File Output Options")
        bool_row("-outputtiff", self.adv_outputtiff)
        bool_row("-outputlzw", self.adv_outputlzw)
        bool_row("-outputde5", self.adv_outputde5)
        flag_row(
            "-moviebitrate",
            self.adv_moviebitrate_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_moviebitrate,
                values=list(self.MOVIE_BITRATE_OPTIONS.keys()),
                state="readonly",
                width=30,
            ),
        )
        bool_row("-movieuncorrected", self.adv_movieuncorrected)
        bool_row("-totalintegrated", self.adv_totalintegrated)
        bool_row("-totalcounted", self.adv_totalcounted)
        flag_row(
            "-totalbitrate",
            self.adv_totalbitrate_enabled,
            lambda p: ttk.Combobox(
                p,
                textvariable=self.adv_totalbitrate,
                values=list(self.TOTAL_BITRATE_OPTIONS.keys()),
                state="readonly",
                width=30,
            ),
        )

        # -intensityhistogram (min max count)
        ttk.Checkbutton(adv_frame, variable=self.adv_intensityhistogram_enabled).grid(
            row=row, column=0, sticky="w", padx=(0, 4)
        )
        ttk.Label(adv_frame, text="-intensityhistogram (min max count):").grid(
            row=row, column=1, sticky="w", pady=2
        )
        ih_f = ttk.Frame(adv_frame)
        ih_f.grid(row=row, column=2, sticky="w", pady=2, padx=(5, 0))
        ttk.Entry(ih_f, textvariable=self.adv_intensityhistogram_min, width=8).pack(
            side="left", padx=(0, 3)
        )
        ttk.Entry(ih_f, textvariable=self.adv_intensityhistogram_max, width=8).pack(
            side="left", padx=(0, 3)
        )
        ttk.Spinbox(
            ih_f, textvariable=self.adv_intensityhistogram_count, from_=1, to=9999, width=7
        ).pack(side="left")
        row += 1

        # -intensityhistogramroi (xo yo xs ys)
        ttk.Checkbutton(adv_frame, variable=self.adv_intensityhistogramroi_enabled).grid(
            row=row, column=0, sticky="w", padx=(0, 4)
        )
        ttk.Label(adv_frame, text="-intensityhistogramroi (xo yo xs ys):").grid(
            row=row, column=1, sticky="w", pady=2
        )
        ihroi_f = ttk.Frame(adv_frame)
        ihroi_f.grid(row=row, column=2, sticky="w", pady=2, padx=(5, 0))
        for rv in (
            self.adv_intensityhistogramroi_xo,
            self.adv_intensityhistogramroi_yo,
            self.adv_intensityhistogramroi_xs,
            self.adv_intensityhistogramroi_ys,
        ):
            ttk.Spinbox(ihroi_f, textvariable=rv, from_=0, to=99999, width=7).pack(
                side="left", padx=(0, 3)
            )
        row += 1

        sep()
        # ── Misc Options ─────────────────────────────────────────────────────
        section("Misc Options")
        bool_row("-quiet", self.adv_quiet)
        bool_row("-silent", self.adv_silent)

    # ── Command building ─────────────────────────────────────────────────────

    def _build_command(self):
        """Assemble and return the full command string."""
        parts = [f'"{self.EXE_PATH}"']

        cam_val = self.CAMERA_OPTIONS.get(self.camera.get(), 8)
        parts.append(f"-camera {cam_val}")
        parts.append("-outputup2")
        parts.append(f"-moviesumframes {self.moviesumframes.get()}")

        if self.singlethread.get():
            parts.append("-singlethread")
        if self.fliphorizontal.get():
            parts.append("-fliphorizontal")
        if self.flipvertical.get():
            parts.append("-flipvertical")

        gr = self.gainreference.get().strip()
        if gr:
            parts.append(
                "-gainreference none" if gr.lower() == "none" else f'-gainreference "{gr}"'
            )

        parts.append(f"-binning {self.binning.get()}")
        parts.append(f"-scanning {self.scanning_x.get()} {self.scanning_y.get()}")

        # ── Advanced options ─────────────────────────────────────────────────
        if self.adv_first_enabled.get():
            parts.append(f"-first {self.adv_first.get()}")
        if self.adv_last_enabled.get():
            parts.append(f"-last {self.adv_last.get()}")
        if self.adv_frametopology_enabled.get():
            parts.append(
                f"-frametopology {self.FRAME_TOPOLOGY_OPTIONS[self.adv_frametopology.get()]}"
            )
        if self.adv_framesperbuffer_enabled.get():
            parts.append(f"-framesperbuffer {self.adv_framesperbuffer.get()}")
        if self.adv_hardwarebinning.get():
            parts.append("-hardwarebinning")
        if self.adv_hardwareroioffset_enabled.get():
            parts.append(
                f"-hardwareroioffset {self.adv_hardwareroioffset_x.get()} {self.adv_hardwareroioffset_y.get()}"
            )
        if self.adv_globalshutter.get():
            parts.append("-globalshutter")
        if self.adv_offchipcds.get():
            parts.append("-offchipcds")
        if self.adv_hdrlevels_enabled.get():
            parts.append(f"-hdrlevels {self.adv_hdrlevels.get()}")
        if self.adv_okra_enabled.get():
            parts.append(f"-okra {self.OKRA_OPTIONS[self.adv_okra.get()]}")
        if self.adv_metadataxml_enabled.get() and self.adv_metadataxml.get():
            parts.append(f'-metadataxml "{self.adv_metadataxml.get()}"')

        if self.adv_acquisitiontype_enabled.get():
            parts.append(
                f"-acquisitiontype {self.ACQUISITION_TYPE_OPTIONS[self.adv_acquisitiontype.get()]}"
            )
        if self.adv_aduperevent_enabled.get():
            parts.append(f"-aduperevent {self.adv_aduperevent.get()}")

        if self.adv_thresholdingtype_enabled.get():
            parts.append(
                f"-thresholdingtype {self.THRESHOLDING_TYPE_OPTIONS[self.adv_thresholdingtype.get()]}"
            )
        if self.adv_adaptivethresholding_enabled.get():
            parts.append(
                f"-adaptivethresholding {self.ADAPTIVE_THRESHOLDING_OPTIONS[self.adv_adaptivethresholding.get()]}"
            )
        if self.adv_threshold_enabled.get():
            parts.append(f"-threshold {self.adv_threshold.get()}")

        if self.adv_thresholdhdr1_enabled.get():
            parts.append(f"-thresholdhdr1 {self.adv_thresholdhdr1.get()}")
        if self.adv_thresholdhdr2_enabled.get():
            parts.append(f"-thresholdhdr2 {self.adv_thresholdhdr2.get()}")
        if self.adv_hdrmergemin0_enabled.get():
            parts.append(f"-hdrmergemin0 {self.adv_hdrmergemin0.get()}")
        if self.adv_hdrmergemax0_enabled.get():
            parts.append(f"-hdrmergemax0 {self.adv_hdrmergemax0.get()}")
        if self.adv_hdrmergemin1_enabled.get():
            parts.append(f"-hdrmergemin1 {self.adv_hdrmergemin1.get()}")
        if self.adv_hdrmergemax1_enabled.get():
            parts.append(f"-hdrmergemax1 {self.adv_hdrmergemax1.get()}")
        if self.adv_hdrgainfactor1_enabled.get():
            parts.append(f"-hdrgainfactor1 {self.adv_hdrgainfactor1.get()}")
        if self.adv_hdrgainfactor2_enabled.get():
            parts.append(f"-hdrgainfactor2 {self.adv_hdrgainfactor2.get()}")

        if self.adv_counting_enabled.get():
            parts.append(f"-counting {self.COUNTING_OPTIONS[self.adv_counting.get()]}")
        if self.adv_eventthresholdmin_enabled.get():
            parts.append(f"-eventthresholdmin {self.adv_eventthresholdmin.get()}")
        if self.adv_eventthresholdmax_enabled.get():
            parts.append(f"-eventthresholdmax {self.adv_eventthresholdmax.get()}")

        if self.adv_processframesperbuffer_enabled.get():
            parts.append(f"-processframesperbuffer {self.adv_processframesperbuffer.get()}")
        if self.adv_processoutputbuffersize_enabled.get():
            parts.append(f"-processoutputbuffersize {self.adv_processoutputbuffersize.get()}")
        if self.adv_simulateinput.get():
            parts.append("-simulateinput")

        for attr, flag in [
            ("adv_darkreference", "-darkreference"),
            ("adv_darkreferencehdr1", "-darkreferencehdr1"),
            ("adv_darkreferencehdr2", "-darkreferencehdr2"),
            ("adv_darkreferenceoffchipcds", "-darkreferenceoffchipcds"),
            ("adv_gainreferencehdr1", "-gainreferencehdr1"),
            ("adv_gainreferencehdr2", "-gainreferencehdr2"),
            ("adv_gainreferencecounting", "-gainreferencecounting"),
        ]:
            if getattr(self, f"{attr}_enabled").get() and getattr(self, attr).get():
                parts.append(f'{flag} "{getattr(self, attr).get()}"')

        if self.adv_badpixelsxml_enabled.get() and self.adv_badpixelsxml.get():
            parts.append(f'-badpixelsxml "{self.adv_badpixelsxml.get()}"')
        if self.adv_badpixelsoutput.get():
            parts.append("-badpixelsoutput")

        if self.adv_binningmethod_enabled.get():
            parts.append(
                f"-binningmethod {self.BINNING_METHOD_OPTIONS[self.adv_binningmethod.get()]}"
            )
        if self.adv_rotation_enabled.get():
            rot_val = self.ROTATION_OPTIONS[self.adv_rotation.get()]
            if rot_val is not None:
                parts.append(f"-rotation {rot_val}")
        if self.adv_roi_enabled.get():
            parts.append(
                f"-roi {self.adv_roi_xoffset.get()} {self.adv_roi_yoffset.get()} "
                f"{self.adv_roi_xsize.get()} {self.adv_roi_ysize.get()}"
            )
        if self.adv_multiply_enabled.get():
            parts.append(f"-multiply {self.adv_multiply.get()}")

        if self.adv_scanningcroptop_enabled.get():
            parts.append(f"-scanningcroptop {self.adv_scanningcroptop.get()}")
        if self.adv_scanningcropbottom_enabled.get():
            parts.append(f"-scanningcropbottom {self.adv_scanningcropbottom.get()}")
        if self.adv_scanningcropleft_enabled.get():
            parts.append(f"-scanningcropleft {self.adv_scanningcropleft.get()}")
        if self.adv_scanningcropright_enabled.get():
            parts.append(f"-scanningcropright {self.adv_scanningcropright.get()}")
        if (
            self.adv_scanningvacuumref_enabled.get()
            and self.adv_scanningvacuumref_x.get()
            and self.adv_scanningvacuumref_y.get()
        ):
            parts.append(
                f'-scanningvacuumref "{self.adv_scanningvacuumref_x.get()}" '
                f'"{self.adv_scanningvacuumref_y.get()}"'
            )

        if self.adv_virtualimage0_enabled.get():
            parts.append(
                f"-virtualimage0 {self.VIRTUAL_IMAGE_METHODS[self.adv_virtualimage0_method.get()]}"
            )
        for i in range(1, 5):
            en = getattr(self, f"adv_virtualimage{i}_enabled").get()
            mask = getattr(self, f"adv_virtualimage{i}_mask").get()
            meth = getattr(self, f"adv_virtualimage{i}_method").get()
            if en and mask:
                parts.append(
                    f'-virtualimage{i} "{mask}" {self.VIRTUAL_IMAGE_METHODS[meth]}'
                )

        if self.adv_outputtiff.get():
            parts.append("-outputtiff")
        if self.adv_outputlzw.get():
            parts.append("-outputlzw")
        if self.adv_outputde5.get():
            parts.append("-outputde5")
        if self.adv_moviebitrate_enabled.get():
            parts.append(f"-moviebitrate {self.MOVIE_BITRATE_OPTIONS[self.adv_moviebitrate.get()]}")
        if self.adv_movieuncorrected.get():
            parts.append("-movieuncorrected")
        if self.adv_totalintegrated.get():
            parts.append("-totalintegrated")
        if self.adv_totalcounted.get():
            parts.append("-totalcounted")
        if self.adv_totalbitrate_enabled.get():
            parts.append(
                f"-totalbitrate {self.TOTAL_BITRATE_OPTIONS[self.adv_totalbitrate.get()]}"
            )
        if self.adv_intensityhistogram_enabled.get():
            parts.append(
                f"-intensityhistogram {self.adv_intensityhistogram_min.get()} "
                f"{self.adv_intensityhistogram_max.get()} "
                f"{self.adv_intensityhistogram_count.get()}"
            )
        if self.adv_intensityhistogramroi_enabled.get():
            parts.append(
                f"-intensityhistogramroi {self.adv_intensityhistogramroi_xo.get()} "
                f"{self.adv_intensityhistogramroi_yo.get()} "
                f"{self.adv_intensityhistogramroi_xs.get()} "
                f"{self.adv_intensityhistogramroi_ys.get()}"
            )

        if self.adv_quiet.get():
            parts.append("-quiet")
        if self.adv_silent.get():
            parts.append("-silent")

        # Input file — always last
        mrc = self.mrc_file_path.get().strip()
        if mrc:
            parts.append(f'"{mrc}"')

        return " ".join(parts)

    def _update_command_preview(self):
        """Refresh the command preview text box."""
        cmd = self._build_command()
        self.cmd_text.config(state="normal")
        self.cmd_text.delete("1.0", "end")
        self.cmd_text.insert("1.0", cmd)
        self.cmd_text.config(state="disabled")

    # ── File dialogs ──────────────────────────────────────────────────────────

    def _browse_mrc(self):
        path = filedialog.askopenfilename(
            filetypes=[("MRC files", "*.mrc"), ("All files", "*.*")]
        )
        if path:
            self.mrc_file_path.set(path)

    def _browse_gainref(self):
        path = filedialog.askopenfilename(
            filetypes=[("MRC/TIFF files", "*.mrc *.tif *.tiff"), ("All files", "*.*")]
        )
        if path:
            self.gainreference.set(path)

    def _browse_any(self, var, filetypes):
        path = filedialog.askopenfilename(filetypes=filetypes)
        if path:
            var.set(path)

    # ── Actions ───────────────────────────────────────────────────────────────

    def _copy_command(self):
        cmd = self._build_command()
        self.root.clipboard_clear()
        self.root.clipboard_append(cmd)
        self._log("Command copied to clipboard.")

    def _run(self):
        mrc = self.mrc_file_path.get().strip()
        if not mrc:
            messagebox.showerror("Error", "Please select an input MRC file.")
            return
        if not os.path.exists(mrc):
            messagebox.showerror("Error", f"Input file does not exist:\n{mrc}")
            return

        cmd = self._build_command()
        self._log(f"Running: {cmd}")
        self.run_button.config(state="disabled")
        threading.Thread(target=self._run_worker, args=(cmd,), daemon=True).start()

    def _run_worker(self, cmd):
        try:
            proc = subprocess.Popen(
                cmd,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
            )
            for line in proc.stdout:
                self._log_threadsafe(line.rstrip())
            proc.wait()
            if proc.returncode == 0:
                self._log_threadsafe("Done.")
            else:
                self._log_threadsafe(f"Process exited with code {proc.returncode}.")
        except Exception as exc:
            self._log_threadsafe(f"Error: {exc}")
        finally:
            self.root.after(0, lambda: self.run_button.config(state="normal"))

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, message):
        self.log_text.config(state="normal")
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")
        self.log_text.config(state="disabled")

    def _log_threadsafe(self, message):
        self.root.after(0, lambda: self._log(message))


def main():
    root = tk.Tk()
    UP2GeneratorGui(root)
    root.mainloop()


if __name__ == "__main__":
    main()
