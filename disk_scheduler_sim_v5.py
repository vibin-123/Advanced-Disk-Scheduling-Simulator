"""
Disk Scheduling Simulator
=========================
Bright-retro theme matching disk_scheduler.html.
Algorithms : FCFS · SSTF · SCAN · C-SCAN
Scaling    : auto-detects screen size; all fonts, margins, and widget
             positions are derived from a single scale factor S.

Dependencies: matplotlib, numpy  (pip install matplotlib numpy)

──────────────────────────────────────────────────────────────
CHANGING THE BACKEND
  If the window does not appear, edit the line below:
      matplotlib.use('TkAgg')
  and try one of: Qt5Agg  |  Qt6Agg  |  WXAgg  |  MacOSX
──────────────────────────────────────────────────────────────
"""

# ── Backend (edit here if needed) ─────────────────────────────────────────────
import matplotlib
matplotlib.use('TkAgg')

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from matplotlib.widgets import Button, TextBox, CheckButtons
from matplotlib import rcParams
import matplotlib.ticker as ticker
import numpy as np
from datetime import datetime
import warnings
import logging

warnings.filterwarnings('ignore')
logging.basicConfig(
    filename='disk_scheduler.log', level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# ──────────────────────────────────────────────────────────────────────────────
#  SCREEN DETECTION  — returns (width_px, height_px, dpi)
# ──────────────────────────────────────────────────────────────────────────────

def _detect_screen():
    """Try several backends to get physical screen dimensions."""
    # 1. tkinter
    try:
        import tkinter as tk
        r = tk.Tk(); r.withdraw()
        sw, sh, dpi = r.winfo_screenwidth(), r.winfo_screenheight(), r.winfo_fpixels('1i')
        r.destroy()
        return int(sw), int(sh), float(dpi)
    except Exception:
        pass
    # 2. Qt5
    try:
        from PyQt5.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        scr = app.primaryScreen()
        geo = scr.geometry()
        dpi = scr.logicalDotsPerInch()
        return geo.width(), geo.height(), float(dpi)
    except Exception:
        pass
    # 3. Qt6
    try:
        from PyQt6.QtWidgets import QApplication
        import sys
        app = QApplication.instance() or QApplication(sys.argv)
        scr = app.primaryScreen()
        geo = scr.geometry()
        dpi = scr.logicalDotsPerInch()
        return geo.width(), geo.height(), float(dpi)
    except Exception:
        pass
    # Fallback: assume a common 1080p laptop
    return 1920, 1080, 96.0


# ──────────────────────────────────────────────────────────────────────────────
#  SCALE COMPUTATION
# ──────────────────────────────────────────────────────────────────────────────

def _compute_scale():
    """
    Returns (fig_w_in, fig_h_in, S) where S is a dimensionless scale factor.
    S == 1.0  →  designed for a 15.6" FHD (1920×1080 @ 96 dpi) display.
    S <  1.0  →  smaller screen (laptop 13–14 inch).
    S >  1.0  →  large external monitor.
    """
    sw, sh, dpi = _detect_screen()
    # Use 90 % of screen width and 84 % of screen height
    fig_w = (sw * 0.90) / dpi
    fig_h = (sh * 0.84) / dpi
    # Hard clamps so the figure is never absurdly small or large
    fig_w = max(9.0,  min(24.0, fig_w))
    fig_h = max(5.5,  min(14.0, fig_h))
    # Reference height = 9.5 inches (1080p @ 96 dpi, 84 %)
    S = fig_h / 9.5
    return fig_w, fig_h, S


FIG_W, FIG_H, S = _compute_scale()

# ──────────────────────────────────────────────────────────────────────────────
#  TYPOGRAPHY  (DejaVu family — available on every platform)
# ──────────────────────────────────────────────────────────────────────────────

F_RETRO = 'DejaVu Sans Mono'   # Courier-style retro font for buttons / labels
F_MONO  = 'DejaVu Sans Mono'   # monospace for numbers
F_SANS  = 'DejaVu Sans'        # clean sans for body text
F_SERIF = 'DejaVu Serif'       # serif for the large title

# ── Scaled font sizes ──────────────────────────────────────────────────────────
def _fs(base):
    """Return a font size scaled by S, clamped to a readable minimum."""
    return max(5.5, round(base * S, 1))

FS = {
    'title':      _fs(20),    # main "DISK SCHEDULER" heading
    'subtitle':   _fs(7),     # sub-heading line
    'pill':       _fs(7.5),   # algorithm badge pills
    'card_head':  _fs(7.5),   # dark header strip on each card
    'axis_lbl':   _fs(7.5),   # x / y axis labels
    'tick':       _fs(6.5),   # tick labels
    'widget_lbl': _fs(7.5),   # TextBox labels
    'widget_val': _fs(8),     # TextBox values
    'btn':        _fs(9),     # RUN button
    'btn_sm':     _fs(8),     # smaller buttons (RESET, presets)
    'status':     _fs(7.5),   # status bar text
    'sum_head':   _fs(8),     # summary section headings
    'sum_body':   _fs(7.5),   # summary body text
    'legend':     _fs(7),     # legend labels
    'annotation': _fs(7.5),   # inline annotations on plots
}

# ── Apply global rcParams ──────────────────────────────────────────────────────
plt.style.use('default')
rcParams.update({
    'font.family':      F_RETRO,
    'font.size':        FS['axis_lbl'],
    'axes.titlesize':   FS['card_head'],
    'axes.labelsize':   FS['axis_lbl'],
    'xtick.labelsize':  FS['tick'],
    'ytick.labelsize':  FS['tick'],
    'figure.dpi':       100,
})

# ──────────────────────────────────────────────────────────────────────────────
#  COLOUR PALETTE  (1-to-1 from disk_scheduler.html CSS variables)
# ──────────────────────────────────────────────────────────────────────────────

C = {
    'bg':          '#F2F1ED',
    'surface':     '#FAFAF7',
    'card':        '#FFFFFF',
    'ink':         '#16161D',
    'ink-mid':     '#4A4A5A',
    'ink-dim':     '#9090A0',
    'border-soft': '#D8D6CF',
    'grid':        '#E8E5DC',
    'amber':       '#E9A100',
    'amber-bg':    '#FFF8E6',
    'amber-dk':    '#B37A00',
    'blue':        '#1D6AE5',
    'blue-bg':     '#EEF4FF',
    'green':       '#1A9E5A',
    'green-bg':    '#EDFAF3',
    'red':         '#D93A2B',
    # Algorithm line colours
    'algo_fcfs':   '#D93A2B',
    'algo_sstf':   '#1D6AE5',
    'algo_scan':   '#E9A100',
    'algo_cscan':  '#1A9E5A',
}
CARD_HEAD_BG   = C['ink']
CARD_HEAD_TEXT = '#FFF5D6'

# ──────────────────────────────────────────────────────────────────────────────
#  LAYOUT CONSTANTS  (all derived from S so they scale with screen)
# ──────────────────────────────────────────────────────────────────────────────
#
#  Figure vertical zones (figure-fraction, bottom = 0, top = 1):
#
#   ┌─────────────────────────────────────────┐  1.000
#   │  header zone  (title + rule + pills)    │  0.930 ─ 1.000
#   ├─────────────────────────────────────────┤  0.930
#   │  GridSpec  (6 plots + summary)          │  0.200 ─ 0.930
#   ├─────────────────────────────────────────┤  0.200
#   │  control row 1  (RUN/RESET + inputs)    │  0.125 ─ 0.195
#   │  control row 2  (SCAN dir + presets)    │  0.050 ─ 0.120
#   ├─────────────────────────────────────────┤  0.050
#   │  status bar                             │  0.005 ─ 0.045
#   └─────────────────────────────────────────┘  0.000

HDR_TOP    = 1.000
HDR_BOT    = 0.930
GS_TOP     = 0.925
GS_BOT     = 0.205
CTRL1_TOP  = 0.195
CTRL1_BOT  = 0.125
CTRL2_TOP  = 0.120
CTRL2_BOT  = 0.050
STAT_Y     = 0.018

# Control element heights / derived
CTRL_H     = CTRL1_TOP - CTRL1_BOT        # ≈ 0.070
CTRL2_H    = CTRL2_TOP - CTRL2_BOT        # ≈ 0.070
BTN_Y      = CTRL1_BOT + CTRL_H * 0.12   # vertical centre of row-1 elements
BTN_H      = CTRL_H * 0.78
INP_Y      = BTN_Y + BTN_H * 0.08
INP_H      = BTN_H * 0.82
PR_Y       = CTRL2_BOT + CTRL2_H * 0.12  # preset row y
PR_H       = CTRL2_H * 0.78

# ──────────────────────────────────────────────────────────────────────────────
#  SHARED AXIS STYLER
# ──────────────────────────────────────────────────────────────────────────────

def style_ax(ax, title='', spine_color=None):
    sc = spine_color or C['ink']
    ax.set_facecolor(C['surface'])
    ax.tick_params(colors=C['ink-dim'], labelsize=FS['tick'], length=2.5)
    ax.grid(True, color=C['grid'], linestyle='--', linewidth=0.55, alpha=0.9)
    ax.set_axisbelow(True)
    for sp in ax.spines.values():
        sp.set_linewidth(max(1.0, 1.6 * S))
        sp.set_color(sc)
    if title:
        ax.set_title(
            title.upper(), color=CARD_HEAD_TEXT,
            fontsize=FS['card_head'], fontfamily=F_RETRO,
            fontweight='bold', pad=_fs(5), loc='left',
            bbox=dict(facecolor=CARD_HEAD_BG, edgecolor='none',
                      pad=_fs(3.5), boxstyle='square,pad=0.28')
        )
    ax.xaxis.set_major_locator(ticker.MaxNLocator(5, integer=True))
    ax.yaxis.set_major_locator(ticker.MaxNLocator(5))
    ax.set_xlabel('Step',     color=C['ink-mid'], fontsize=FS['axis_lbl'], fontfamily=F_RETRO)
    ax.set_ylabel('Cylinder', color=C['ink-mid'], fontsize=FS['axis_lbl'], fontfamily=F_RETRO)
    plt.setp(ax.get_xticklabels(), fontfamily=F_MONO, color=C['ink-dim'])
    plt.setp(ax.get_yticklabels(), fontfamily=F_MONO, color=C['ink-dim'])


# ──────────────────────────────────────────────────────────────────────────────
#  MAIN CLASS
# ──────────────────────────────────────────────────────────────────────────────

class DiskSchedulingSimulator:
    """
    Layout (4-row × 3-col GridSpec):
    ┌──────────────┬──────────────┬──────────────────┐  row 0
    │  seek_path   │  comparison  │                  │
    ├──────────────┼──────────────┤    summary       │  row 1
    │     fcfs     │    sstf      │  (rows 0–2)      │
    ├──────────────┼──────────────┤                  │  row 2
    │     scan     │    cscan     │                  │
    ├──────────────┴──────────────┴──────────────────┤  row 3
    │           controls (hidden GridSpec row)        │
    └────────────────────────────────────────────────┘
    """

    PRESETS = {
        'Classic':    {'disk': 200, 'head': 53,  'reqs': [98,183,37,122,14,124,65,67]},
        'Scattered':  {'disk': 200, 'head': 100, 'reqs': [5,195,10,190,15,185,20,180,50,150]},
        'Clustered':  {'disk': 200, 'head': 100, 'reqs': [88,90,95,92,87,103,98,91,85,105]},
        'Sequential': {'disk': 200, 'head': 0,   'reqs': [10,20,30,40,50,60,70,80,90,100,110,120,130]},
    }

    ALGO_DESC = {
        'FCFS':   'Arrival order. Baseline.\nWorst average seek.',
        'SSTF':   'Nearest cylinder first.\nFast but may starve.',
        'SCAN':   'Elevator sweep to end\nthen reverses.',
        'C-SCAN': 'One-way sweep; wraps\nto 0 for uniform wait.',
    }

    # ── init ─────────────────────────────────────────────────────────────────

    def __init__(self):
        self.disk_size     = 200
        self.head_position = 53
        self.requests      = [98, 183, 37, 122, 14, 124, 65, 67]
        self.scan_dir      = 'up'
        self.results       = {}
        self.sim_count     = 0
        self.last_run_time = None
        self._ui_locked    = False

        self._build()
        logging.info(f'DiskSchedulingSimulator init — fig {FIG_W:.1f}×{FIG_H:.1f}" S={S:.2f}')

    # ══════════════════════════════════════════════════════════════════════════
    #  BUILD
    # ══════════════════════════════════════════════════════════════════════════

    def _build(self):
        # ── Figure ────────────────────────────────────────────────────────────
        self.fig = plt.figure(figsize=(FIG_W, FIG_H), facecolor=C['bg'])
        self.fig.canvas.manager.set_window_title('Disk Scheduling Simulator')

        # ── Project name — top-left (replaces logo) ───────────────────────────
        self._draw_project_name()

        # ── Centred title ──────────────────────────────────────────────────────
        self.fig.text(
            0.50, 0.976,
            'DISK SCHEDULING SIMULATOR',
            ha='center', va='top',
            fontfamily=F_RETRO, fontsize=FS['title'],
            fontweight='bold', color=C['ink'],
        )
        self.fig.text(
            0.50, 0.955,
            'I/O SEEK ALGORITHM VISUALIZER  ·  PERFORMANCE ANALYZER',
            ha='center', va='top',
            fontfamily=F_RETRO, fontsize=FS['subtitle'],
            fontweight='bold', color=C['ink-mid'], alpha=0.75,
        )

        # ── Algorithm badge pills (top-right) ─────────────────────────────────
        self._draw_pills()

        # ── Horizontal rule below header ───────────────────────────────────────
        self.fig.add_artist(mpatches.FancyArrowPatch(
            (0.02, HDR_BOT + 0.002), (0.98, HDR_BOT + 0.002),
            transform=self.fig.transFigure,
            arrowstyle='-', color=C['ink'], linewidth=max(1.0, 1.8 * S),
        ))

        # ── GridSpec for the 6 plot panels + summary ──────────────────────────
        self.gs = GridSpec(
            3, 3, figure=self.fig,
            left=0.05, right=0.98,
            bottom=GS_BOT, top=GS_TOP,
            hspace=max(0.55, 0.65 * S),
            wspace=max(0.28, 0.32 * S),
        )

        self.axes = {
            'seek_path':  self.fig.add_subplot(self.gs[0, 0], facecolor=C['surface']),
            'comparison': self.fig.add_subplot(self.gs[0, 1], facecolor=C['surface']),
            'fcfs':       self.fig.add_subplot(self.gs[1, 0], facecolor=C['surface']),
            'sstf':       self.fig.add_subplot(self.gs[1, 1], facecolor=C['surface']),
            'scan':       self.fig.add_subplot(self.gs[2, 0], facecolor=C['surface']),
            'cscan':      self.fig.add_subplot(self.gs[2, 1], facecolor=C['surface']),
            'summary':    self.fig.add_subplot(self.gs[0:3, 2], facecolor=C['card']),
        }

        self._style_all_axes()

        # ── Thin rules separating control rows ────────────────────────────────
        for rule_y in [CTRL1_TOP + 0.005, CTRL2_TOP + 0.003, STAT_Y + 0.028]:
            self.fig.add_artist(mpatches.FancyArrowPatch(
                (0.02, rule_y), (0.98, rule_y),
                transform=self.fig.transFigure,
                arrowstyle='-', color=C['border-soft'], linewidth=0.8,
            ))

        # ── Control rows ──────────────────────────────────────────────────────
        self._build_row1()   # RUN / RESET / Disk / Head / Queue
        self._build_row2()   # SCAN DIR + Presets

        # ── Status bar ────────────────────────────────────────────────────────
        self._build_status_bar()

        # ── Initial content ───────────────────────────────────────────────────
        self._draw_empty()
        self._update_summary()

    # ── Project name (top-left) ───────────────────────────────────────────────

    def _draw_project_name(self):
        """
        Two-line project name in the header, top-left.
        Replaces the previous floppy disk logo.
        """
        # Main word — bold ink
        self.fig.text(
            0.022, 0.984,
            'DISK',
            ha='left', va='top',
            fontfamily=F_RETRO, fontsize=_fs(14),
            fontweight='bold', color=C['ink'],
        )
        # Second word — amber accent
        self.fig.text(
            0.022, 0.960,
            'SCHED',
            ha='left', va='top',
            fontfamily=F_RETRO, fontsize=_fs(10),
            fontweight='bold', color=C['amber'],
        )
        # Thin vertical accent bar (mimics HTML left-border accent)
        self.fig.add_artist(mpatches.FancyBboxPatch(
            (0.017, 0.950), 0.003, 0.046,
            boxstyle='square,pad=0',
            transform=self.fig.transFigure,
            facecolor=C['amber'], edgecolor='none', zorder=5,
        ))

    # ── Pill badges ───────────────────────────────────────────────────────────

    def _draw_pills(self):
        labels = ['FCFS', 'SSTF', 'SCAN', 'C-SCAN']
        pill_w = 0.048
        pill_h = 0.026
        pill_gap = 0.004
        total_w = len(labels) * pill_w + (len(labels) - 1) * pill_gap
        x_start = 0.98 - total_w

        for i, lbl in enumerate(labels):
            x = x_start + i * (pill_w + pill_gap)
            pax = self.fig.add_axes([x, HDR_BOT + 0.006, pill_w, pill_h])
            pax.set_facecolor(C['card'])
            pax.set_xlim(0, 1); pax.set_ylim(0, 1)
            pax.axis('off')
            for sp in pax.spines.values():
                sp.set_visible(True)
                sp.set_linewidth(max(1.0, 1.6 * S))
                sp.set_color(C['ink'])
            pax.text(0.5, 0.5, lbl, ha='center', va='center',
                     fontfamily=F_RETRO, fontsize=FS['pill'],
                     fontweight='bold', color=C['ink'])

    # ── Axis styling ──────────────────────────────────────────────────────────

    def _style_all_axes(self):
        cfgs = [
            ('seek_path',  'Seek Path — All Algorithms',  None),
            ('comparison', 'Total Seek Distance',          None),
            ('fcfs',       'FCFS — Seek Sequence',         C['algo_fcfs']),
            ('sstf',       'SSTF — Seek Sequence',         C['algo_sstf']),
            ('scan',       'SCAN — Seek Sequence',         C['algo_scan']),
            ('cscan',      'C-SCAN — Seek Sequence',       C['algo_cscan']),
        ]
        for key, title, sc in cfgs:
            style_ax(self.axes[key], title=title, spine_color=sc or C['ink'])

        ax_s = self.axes['summary']
        ax_s.set_facecolor(C['card']); ax_s.axis('off')
        for sp in ax_s.spines.values():
            sp.set_linewidth(max(1.0, 1.6 * S))
            sp.set_color(C['ink'])

    # ══════════════════════════════════════════════════════════════════════════
    #  CONTROL ROW 1 — RUN  RESET  Disk  Head  Queue
    # ══════════════════════════════════════════════════════════════════════════

    def _build_row1(self):
        """
        Proportional layout: all elements fitted within [0.02, 0.98].
        Widths are fractions of total figure width so they scale.
        """
        lx   = 0.02
        y    = BTN_Y
        h    = BTN_H
        ih   = INP_H
        iy   = INP_Y

        # Wider controls so labels never crowd or clip.
        run_w   = 0.078
        rst_w   = 0.072
        disk_w  = 0.098
        head_w  = 0.098
        queue_w = 0.285
        gap1, gap2, gap3, gap4 = 0.008, 0.012, 0.008, 0.008

        slots = [
            ('run',   run_w),
            ('_gap1', gap1),
            ('rst',   rst_w),
            ('_gap2', gap2),
            ('disk',  disk_w),
            ('_gap3', gap3),
            ('head',  head_w),
            ('_gap4', gap4),
            ('queue', queue_w),
        ]

        x = lx
        positions = {}
        widths = {}
        for name, w in slots:
            positions[name] = x
            widths[name] = w
            x += w

        # ── ▶ RUN ─────────────────────────────────────────────────────────────
        ax_run = self.fig.add_axes([positions['run'], y, widths['run'], h])
        self._sw(ax_run, bg=C['ink'])
        self.btn_run = Button(ax_run, '▶  RUN', color=C['ink'], hovercolor='#2C2C3C')
        self.btn_run.label.set_color(C['amber'])
        self.btn_run.label.set_fontfamily(F_RETRO)
        self.btn_run.label.set_fontweight('bold')
        self.btn_run.label.set_fontsize(FS['btn'])
        self.btn_run.on_clicked(self.run_simulation)

        # ── RESET ─────────────────────────────────────────────────────────────
        ax_rst = self.fig.add_axes([positions['rst'], y, widths['rst'], h])
        self._sw(ax_rst)
        self.btn_rst = Button(ax_rst, 'RESET', color=C['card'], hovercolor=C['amber-bg'])
        self.btn_rst.label.set_color(C['ink'])
        self.btn_rst.label.set_fontfamily(F_RETRO)
        self.btn_rst.label.set_fontweight('bold')
        self.btn_rst.label.set_fontsize(max(FS['btn_sm'] - 0.5, 6.5))
        self.btn_rst.on_clicked(self.reset)

        # ── Disk size ─────────────────────────────────────────────────────────
        ax_d = self.fig.add_axes([positions['disk'], iy, widths['disk'], ih])
        self._sw(ax_d, border_color=C['border-soft'])
        self.tb_disk = TextBox(ax_d, 'Disk: ', initial='200',
                               color=C['surface'], hovercolor=C['surface'],
                               label_pad=0.03)
        self._stb(self.tb_disk)
        self.tb_disk.on_submit(self._cb_disk)

        # ── Head position ─────────────────────────────────────────────────────
        ax_h = self.fig.add_axes([positions['head'], iy, widths['head'], ih])
        self._sw(ax_h, border_color=C['border-soft'])
        self.tb_head = TextBox(ax_h, 'Head: ', initial='53',
                               color=C['surface'], hovercolor=C['surface'],
                               label_pad=0.03)
        self._stb(self.tb_head)
        self.tb_head.on_submit(self._cb_head)

        # ── Queue ─────────────────────────────────────────────────────────────
        ax_q = self.fig.add_axes([positions['queue'], iy, widths['queue'], ih])
        self._sw(ax_q, border_color=C['border-soft'])
        self.tb_reqs = TextBox(ax_q, 'Queue: ',
                               initial='98,183,37,122,14,124,65,67',
                               color=C['surface'], hovercolor=C['surface'],
                               label_pad=0.02)
        self._stb(self.tb_reqs)
        self.tb_reqs.on_submit(self._cb_reqs)

        # Row-1 labels above inputs, centered over each field.
        lbl_y = CTRL1_TOP + 0.0035
        for txt, x0, w in [
            ('DISK SIZE', positions['disk'], widths['disk']),
            ('HEAD START', positions['head'], widths['head']),
            ('REQUEST QUEUE', positions['queue'], widths['queue']),
        ]:
            self.fig.text(x0 + w / 2, lbl_y, txt,
                          color=C['ink-dim'], fontsize=_fs(5.8),
                          fontfamily=F_RETRO, fontweight='bold',
                          ha='center', va='bottom')

    # ══════════════════════════════════════════════════════════════════════════
    #  CONTROL ROW 2 — SCAN Direction  +  Presets
    # ══════════════════════════════════════════════════════════════════════════

    def _build_row2(self):
        y  = PR_Y
        h  = PR_H
        lx = 0.02

        # ── Row-2 section labels ───────────────────────────────────────────────
        lbl_y = CTRL2_TOP + 0.0035
        self.fig.text(lx + 0.075, lbl_y, 'SCAN DIRECTION',
                      color=C['ink-dim'], fontsize=_fs(5.8),
                      fontfamily=F_RETRO, fontweight='bold',
                      ha='center', va='bottom')
        self.fig.text(0.625, lbl_y, 'PRESETS',
                      color=C['ink-dim'], fontsize=_fs(5.8),
                      fontfamily=F_RETRO, fontweight='bold',
                      ha='center', va='bottom')

        # ── SCAN Direction CheckButtons ────────────────────────────────────────
        ax_dir = self.fig.add_axes([lx, y, 0.150, h])
        self._sw(ax_dir)
        self.chk_dir = CheckButtons(
            ax=ax_dir,
            labels=['  ↑ Toward High', '  ↓ Toward Low'],
            actives=[True, False],
            label_props={
                'color':    [C['ink'], C['ink-mid']],
                'fontsize': [FS['btn_sm'], FS['btn_sm']],
            },
            frame_props={'edgecolor': [C['ink'], C['border-soft']]},
            check_props={'color': [C['amber'], C['ink-dim']]},
        )
        self.chk_dir.on_clicked(self._cb_dir)

        # ── Preset buttons ─────────────────────────────────────────────────────
        presets   = list(self.PRESETS.keys())
        n_pre     = len(presets)
        pre_start = 0.270
        pre_end   = 0.980
        pre_gap   = 0.008
        pre_w     = (pre_end - pre_start - (n_pre - 1) * pre_gap) / n_pre

        self._preset_btns = []
        for i, name in enumerate(presets):
            xp  = pre_start + i * (pre_w + pre_gap)
            axp = self.fig.add_axes([xp, y, pre_w, h])
            self._sw(axp, left_accent=True)
            btn = Button(axp, name, color=C['card'], hovercolor=C['amber-bg'])
            btn.label.set_color(C['ink-mid'])
            btn.label.set_fontfamily(F_RETRO)
            btn.label.set_fontweight('bold')
            btn.label.set_fontsize(FS['btn_sm'])
            p = self.PRESETS[name]
            def _mk(r, h2, d):
                return lambda ev: self._load_preset(r, h2, d)
            btn.on_clicked(_mk(p['reqs'], p['head'], p['disk']))
            self._preset_btns.append(btn)

    # ── Widget helpers ────────────────────────────────────────────────────────

    def _sw(self, ax, bg=None, border_color=None, left_accent=False):
        """Style a widget axes: white card with ink border."""
        ax.set_facecolor(bg or C['card'])
        bc = border_color or C['ink']
        for side, sp in ax.spines.items():
            sp.set_linewidth(max(1.0, 1.6 * S))
            sp.set_color(bc)
            if left_accent and side == 'left':
                sp.set_linewidth(max(2.0, 3.0 * S))
                sp.set_color(C['amber'])
        ax.tick_params(bottom=False, left=False,
                       labelbottom=False, labelleft=False)

    def _stb(self, tb):
        """Style a TextBox widget."""
        tb.label.set_color(C['ink-mid'])
        tb.label.set_fontfamily(F_RETRO)
        tb.label.set_fontsize(FS['widget_lbl'])
        tb.label.set_fontweight('bold')
        tb.text_disp.set_color(C['ink'])
        tb.text_disp.set_fontfamily(F_MONO)
        tb.text_disp.set_fontsize(FS['widget_val'])

    def _set_textbox_value(self, tb, value):
        """Set a TextBox value without re-entering its submit callback."""
        self._ui_locked = True
        try:
            tb.set_val(str(value))
        finally:
            self._ui_locked = False

    def _sync_checkbuttons(self, target_up: bool):
        """Keep the two direction checkboxes mutually exclusive."""
        status = self.chk_dir.get_status()
        want_up = bool(target_up)
        if want_up and not status[0]:
            self._ui_locked = True
            try:
                self.chk_dir.set_active(0)
            finally:
                self._ui_locked = False
        elif (not want_up) and not status[1]:
            self._ui_locked = True
            try:
                self.chk_dir.set_active(1)
            finally:
                self._ui_locked = False

    # ── Status bar ────────────────────────────────────────────────────────────

    def _build_status_bar(self):
        ys = STAT_Y
        self.txt_ts = self.fig.text(
            0.022, ys, 'Configure parameters and click  ▶ RUN',
            color=C['ink-mid'], fontsize=FS['status'],
            ha='left', fontfamily=F_MONO)
        self.txt_status = self.fig.text(
            0.440, ys, 'Status: [IDLE]',
            color=C['amber-dk'], fontsize=FS['status'],
            ha='left', fontfamily=F_RETRO, fontweight='bold')
        self.txt_runs = self.fig.text(
            0.660, ys, 'Runs: 0',
            color=C['ink-mid'], fontsize=FS['status'],
            ha='left', fontfamily=F_MONO)
        self.txt_best = self.fig.text(
            0.800, ys, 'Best: —',
            color=C['green'], fontsize=FS['status'],
            ha='left', fontfamily=F_RETRO, fontweight='bold')

    def _set_status(self, txt, color=None):
        self.txt_status.set_text(txt)
        if color:
            self.txt_status.set_color(color)

    # ══════════════════════════════════════════════════════════════════════════
    #  INPUT CALLBACKS
    # ══════════════════════════════════════════════════════════════════════════

    def _cb_disk(self, text):
        if self._ui_locked:
            return
        try:
            v = int(text)
            if v < 10: raise ValueError
            self.disk_size = v
            self._set_status(f'Status: [DISK SIZE → {v}]', C['amber-dk'])
        except ValueError:
            self._set_status('Status: [INVALID DISK SIZE]', C['red'])
            self._set_textbox_value(self.tb_disk, self.disk_size)
        self.fig.canvas.draw_idle()

    def _cb_head(self, text):
        if self._ui_locked:
            return
        try:
            v = int(text)
            if not (0 <= v < self.disk_size): raise ValueError
            self.head_position = v
            self._set_status(f'Status: [HEAD → {v}]', C['amber-dk'])
        except ValueError:
            self._set_status(f'Status: [HEAD MUST BE 0–{self.disk_size-1}]', C['red'])
            self._set_textbox_value(self.tb_head, self.head_position)
        self.fig.canvas.draw_idle()

    def _cb_reqs(self, text):
        if self._ui_locked:
            return
        try:
            vals  = [int(t) for t in text.replace(';',' ').replace(',',' ').split() if t]
            valid = [v for v in vals if 0 <= v < self.disk_size]
            if not valid: raise ValueError
            self.requests = valid
            self._set_status(f'Status: [QUEUE — {len(valid)} requests]', C['amber-dk'])
        except (ValueError, AttributeError):
            self._set_status('Status: [INVALID QUEUE]', C['red'])
            self._set_textbox_value(self.tb_reqs, ','.join(map(str, self.requests)))
        self.fig.canvas.draw_idle()

    def _cb_dir(self, label):
        if self._ui_locked:
            return
        if '↑' in label:
            self.scan_dir = 'up'
            self._sync_checkbuttons(True)
        else:
            self.scan_dir = 'down'
            self._sync_checkbuttons(False)
        self._set_status(f'Status: [SCAN DIR → {self.scan_dir.upper()}]', C['amber-dk'])
        self.fig.canvas.draw_idle()

    def _load_preset(self, reqs, head, disk):
        self.requests = list(reqs); self.head_position = head; self.disk_size = disk
        self._set_textbox_value(self.tb_disk, disk)
        self._set_textbox_value(self.tb_head, head)
        self._set_textbox_value(self.tb_reqs, ','.join(map(str, reqs)))
        self._set_status('Status: [PRESET LOADED — click ▶ RUN]', C['amber'])
        self.fig.canvas.draw_idle()

    # ══════════════════════════════════════════════════════════════════════════
    #  ALGORITHMS
    # ══════════════════════════════════════════════════════════════════════════

    @staticmethod
    def _seek(seq):
        return sum(abs(seq[i+1]-seq[i]) for i in range(len(seq)-1))

    def _fcfs(self):
        s = [self.head_position] + list(self.requests)
        return s, self._seek(s)

    def _sstf(self):
        rem = list(self.requests); seq = [self.head_position]; cur = self.head_position
        while rem:
            n = min(rem, key=lambda r: abs(r-cur))
            seq.append(n); cur = n; rem.remove(n)
        return seq, self._seek(seq)

    def _scan(self):
        sr = sorted(self.requests)
        lo = [r for r in sr if r <  self.head_position]
        hi = [r for r in sr if r >= self.head_position]
        order = (hi + [self.disk_size-1] + lo[::-1]) if self.scan_dir=='up' \
                else (lo[::-1] + [0] + hi)
        seq = [self.head_position] + order
        return seq, self._seek(seq)

    def _cscan(self):
        sr = sorted(self.requests)
        hi = [r for r in sr if r >= self.head_position]
        lo = [r for r in sr if r <  self.head_position]
        seq = [self.head_position] + hi + [self.disk_size-1, 0] + lo
        return seq, self._seek(seq)

    # ══════════════════════════════════════════════════════════════════════════
    #  SIMULATION
    # ══════════════════════════════════════════════════════════════════════════

    def run_simulation(self, event=None):
        try:
            self._cb_disk(self.tb_disk.text)
            self._cb_head(self.tb_head.text)
            self._cb_reqs(self.tb_reqs.text)
            if not self.requests:
                self._set_status('Status: [NO VALID REQUESTS]', C['red'])
                self.fig.canvas.draw_idle(); return

            sf, kf  = self._fcfs()
            ss, ks  = self._sstf()
            sc, ksc = self._scan()
            sv, ksv = self._cscan()
            n = len(self.requests)

            self.results = {
                'FCFS':   {'seq': sf,  'seek': kf,  'avg': kf/n,  'color': C['algo_fcfs']},
                'SSTF':   {'seq': ss,  'seek': ks,  'avg': ks/n,  'color': C['algo_sstf']},
                'SCAN':   {'seq': sc,  'seek': ksc, 'avg': ksc/n, 'color': C['algo_scan']},
                'C-SCAN': {'seq': sv,  'seek': ksv, 'avg': ksv/n, 'color': C['algo_cscan']},
            }
            self.sim_count    += 1
            self.last_run_time = datetime.now().strftime('%H:%M:%S')

            self._plot_seek_path()
            self._plot_comparison()
            self._plot_seq('fcfs',  'FCFS — Seek Sequence',   sf,  kf,  C['algo_fcfs'])
            self._plot_seq('sstf',  'SSTF — Seek Sequence',   ss,  ks,  C['algo_sstf'])
            self._plot_seq('scan',  'SCAN — Seek Sequence',   sc,  ksc, C['algo_scan'])
            self._plot_seq('cscan', 'C-SCAN — Seek Sequence', sv,  ksv, C['algo_cscan'])
            self._update_summary()

            best = min(self.results, key=lambda k: self.results[k]['seek'])
            self._set_status('Status: [COMPLETE]', C['green'])
            self.txt_ts.set_text(
                f'Last run: {self.last_run_time}  ·  '
                f'Disk: {self.disk_size}  ·  Head: {self.head_position}  ·  Reqs: {n}'
            )
            self.txt_runs.set_text(f'Runs: {self.sim_count}')
            self.txt_best.set_text(f'Best: {best} ({self.results[best]["seek"]} cyls)')
            self.fig.canvas.draw_idle()
            logging.info(f'Run #{self.sim_count} best={best}')

        except Exception as exc:
            self._set_status(f'Status: [ERROR — {str(exc)[:38]}]', C['red'])
            self.fig.canvas.draw_idle()
            logging.error(f'Error: {exc}', exc_info=True)

    def reset(self, event=None):
        self.results = {}
        self.disk_size = 200; self.head_position = 53
        self.requests  = [98, 183, 37, 122, 14, 124, 65, 67]
        self._set_textbox_value(self.tb_disk, '200')
        self._set_textbox_value(self.tb_head, '53')
        self._set_textbox_value(self.tb_reqs, '98,183,37,122,14,124,65,67')
        self._draw_empty(); self._update_summary()
        self._set_status('Status: [IDLE]', C['amber-dk'])
        self.txt_ts.set_text('Configure parameters and click  ▶ RUN')
        self.txt_best.set_text('Best: —')
        self.fig.canvas.draw_idle()

    # ══════════════════════════════════════════════════════════════════════════
    #  PLOTTING
    # ══════════════════════════════════════════════════════════════════════════

    def _draw_seek_line(self, ax, seq, color, label='',
                        lw=1.8, annotate_last=True):
        steps = list(range(len(seq)))
        ax.plot(steps, seq, color=color, linewidth=lw,
                marker='o', markersize=max(2.5, 3.5*S),
                markerfacecolor=C['surface'],
                markeredgecolor=color,
                markeredgewidth=max(0.8, 1.1*S),
                label=label, zorder=4)
        # Head start diamond
        ax.scatter([0], [seq[0]], color=C['blue'],
                   s=max(25, 45*S), marker='D', zorder=6,
                   linewidths=max(0.8, 1.1*S), edgecolors=C['ink'])
        # Last-point annotation
        if annotate_last and len(seq) > 1:
            ax.annotate(
                f'{seq[-1]}',
                xy=(len(seq)-1, seq[-1]),
                xytext=(6, 0), textcoords='offset points',
                color=color, fontsize=FS['annotation'],
                fontfamily=F_MONO, fontweight='bold',
                bbox=dict(boxstyle='round,pad=0.25',
                          fc=C['surface'], ec=color,
                          lw=max(0.8, 1.0*S), alpha=0.92)
            )

    # ── Panel 1: All algorithms overlaid ─────────────────────────────────────

    def _plot_seek_path(self):
        ax = self.axes['seek_path']
        ax.clear(); style_ax(ax, 'Seek Path — All Algorithms')
        for name, data in self.results.items():
            self._draw_seek_line(ax, data['seq'], data['color'],
                                 label=f"{name} ({data['seek']})",
                                 lw=max(1.2, 1.6*S), annotate_last=False)
        ax.axhline(self.head_position, color=C['blue'],
                   linestyle=':', linewidth=max(0.8, 1.0*S), alpha=0.5,
                   label=f'Head: {self.head_position}')
        ax.set_ylim(-5, self.disk_size + 5)
        ax.set_xlim(0, max(len(d['seq']) for d in self.results.values()) - 1)
        leg = ax.legend(loc='upper right', fontsize=FS['legend'],
                        facecolor=C['card'], edgecolor=C['border-soft'],
                        framealpha=0.95)
        for t in leg.get_texts():
            t.set_fontfamily(F_MONO); t.set_color(C['ink-mid'])

    # ── Panel 2: Bar chart comparison ────────────────────────────────────────

    def _plot_comparison(self):
        ax = self.axes['comparison']
        ax.clear(); style_ax(ax, 'Total Seek Distance')
        ax.set_xlabel('Algorithm', color=C['ink-mid'],
                      fontsize=FS['axis_lbl'], fontfamily=F_RETRO)
        ax.set_ylabel('Seek (cylinders)', color=C['ink-mid'],
                      fontsize=FS['axis_lbl'], fontfamily=F_RETRO)
        ax.set_axisbelow(True)

        names  = list(self.results.keys())
        seeks  = [self.results[n]['seek'] for n in names]
        avgs   = [self.results[n]['avg']   for n in names]
        colors = [self.results[n]['color'] for n in names]
        max_s  = max(seeks); min_s = min(seeks)

        bars = ax.bar(names, seeks, color=colors,
                      edgecolor=C['ink'], linewidth=max(0.8, 1.1*S),
                      width=0.58, zorder=3)

        for bar, val, avg, col in zip(bars, seeks, avgs, colors):
            ax.text(bar.get_x() + bar.get_width()/2,
                    val + max_s * 0.04,
                    str(val), ha='center', va='bottom',
                    fontfamily=F_MONO, fontsize=FS['annotation'],
                    fontweight='bold', color=C['ink'], zorder=5)
            if val > max_s * 0.20:
                ax.text(bar.get_x() + bar.get_width()/2,
                        val * 0.42, f'avg\n{avg:.0f}',
                        ha='center', va='center',
                        fontfamily=F_MONO, fontsize=_fs(6.5),
                        color='white', alpha=0.85, zorder=5)

        bi = seeks.index(min_s)
        bars[bi].set_edgecolor(C['green'])
        bars[bi].set_linewidth(max(1.5, 2.2*S))
        ax.annotate('★ BEST',
                    xy=(bi, min_s), xytext=(bi, min_s + max_s * 0.14),
                    ha='center', fontsize=FS['annotation'],
                    fontweight='bold', fontfamily=F_RETRO,
                    color=C['green'], zorder=6,
                    arrowprops=dict(arrowstyle='->', color=C['green'],
                                    lw=max(1.0, 1.3*S)))
        ax.set_ylim(0, max_s * 1.28)
        plt.setp(ax.get_xticklabels(), fontfamily=F_RETRO,
                 fontweight='bold', color=C['ink-mid'])

    # ── Panels 3–6: Individual algorithm sequence ─────────────────────────────

    def _plot_seq(self, key, title_base, seq, total_seek, color):
        n   = len(self.requests)
        avg = total_seek / n if n else 0
        thr = 100.0 / (avg + 1)
        title = f'{title_base}  ·  {total_seek} cyls  avg {avg:.1f}  thr {thr:.2f}'
        ax = self.axes[key]
        ax.clear(); style_ax(ax, title, spine_color=color)

        steps = list(range(len(seq)))
        ax.fill_between(steps, seq, alpha=0.06, color=color, zorder=1)
        self._draw_seek_line(ax, seq, color, lw=max(1.4, 2.0*S))
        ax.axhline(avg, color=C['ink-dim'],
                   linestyle='--', linewidth=max(0.7, 1.0*S), alpha=0.7,
                   label=f'Avg: {avg:.1f}')
        ax.set_ylim(-5, self.disk_size + 5)
        ax.set_xlim(0, max(1, len(seq) - 1))

        leg = ax.legend(loc='upper right', fontsize=FS['legend'],
                        facecolor=C['card'], edgecolor=C['border-soft'],
                        framealpha=0.92)
        for t in leg.get_texts():
            t.set_fontfamily(F_MONO); t.set_color(C['ink-mid'])

    # ── Summary panel ─────────────────────────────────────────────────────────

    def _update_summary(self):
        ax = self.axes['summary']
        ax.clear(); ax.set_facecolor(C['card']); ax.axis('off')
        ax.set_xlim(0, 1); ax.set_ylim(0, 1)

        # Card-head strip
        ax.add_patch(mpatches.FancyBboxPatch(
            (0, 0.940), 1.0, 0.060,
            boxstyle='square,pad=0', transform=ax.transAxes,
            facecolor=C['ink'], edgecolor='none', zorder=2, clip_on=False))
        ax.text(0.05, 0.968, 'SIMULATION SUMMARY',
                ha='left', va='center', transform=ax.transAxes,
                fontfamily=F_RETRO, fontsize=FS['sum_head'],
                fontweight='bold', color=CARD_HEAD_TEXT, zorder=3)

        # ── PRE-RUN: algorithm descriptions ──────────────────────────────────
        if not self.results:
            colors = [C['algo_fcfs'], C['algo_sstf'],
                      C['algo_scan'], C['algo_cscan']]
            y = 0.88
            for (aname, adesc), acol in zip(self.ALGO_DESC.items(), colors):
                ax.add_patch(mpatches.FancyBboxPatch(
                    (0.02, y-0.080), 0.022, 0.082,
                    boxstyle='square,pad=0', transform=ax.transAxes,
                    facecolor=acol, edgecolor='none', alpha=0.85))
                ax.text(0.07, y, aname,
                        ha='left', va='top', transform=ax.transAxes,
                        fontfamily=F_RETRO, fontsize=FS['sum_head'],
                        fontweight='bold', color=acol)
                ax.text(0.07, y-0.022, adesc,
                        ha='left', va='top', transform=ax.transAxes,
                        fontfamily=F_SANS, fontsize=FS['sum_body'],
                        color=C['ink-mid'], linespacing=1.35)
                y -= 0.215
            return

        # ── POST-RUN: compact table that always lists every algorithm ─────────
        ordered_names = ['FCFS', 'SSTF', 'SCAN', 'C-SCAN']
        best_name = min(self.results, key=lambda k: self.results[k]['seek'])

        def _sec(y, label):
            ax.text(0.04, y, label,
                    ha='left', va='top', transform=ax.transAxes,
                    fontfamily=F_RETRO, fontsize=FS['sum_head'],
                    fontweight='bold', color=C['amber'])
            return y - 0.040

        def _row(y, lbl, val):
            ax.text(0.05, y, lbl+':',
                    ha='left', va='top', transform=ax.transAxes,
                    fontfamily=F_RETRO, fontsize=FS['sum_body'],
                    fontweight='bold', color=C['ink-mid'])
            ax.text(0.42, y, val,
                    ha='left', va='top', transform=ax.transAxes,
                    fontfamily=F_MONO, fontsize=FS['sum_body'],
                    color=C['ink'])
            return y - 0.048

        def _rule(y):
            ax.plot([0.03, 0.97], [y, y], transform=ax.transAxes,
                    color=C['border-soft'], linewidth=0.7)
            return y - 0.020

        y = 0.925
        y = _sec(y, 'PARAMETERS')
        for lbl, val in [
            ('Disk',    f'{self.disk_size} cylinders'),
            ('Head',    str(self.head_position)),
            ('Requests',str(len(self.requests))),
            ('Queue',   ', '.join(map(str, self.requests[:7]))
                        + ('…' if len(self.requests)>7 else '')),
            ('SCAN Dir',self.scan_dir.upper()),
            ('Last Run',self.last_run_time or '—'),
            ('Runs',    str(self.sim_count)),
        ]:
            y = _row(y, lbl, val)

        y = _rule(y)
        y = _sec(y, 'ALGORITHM STATS')

        # Header row
        for x, txt in [(0.06, 'ALG'), (0.41, 'SEEK'), (0.59, 'AVG'), (0.76, 'THR')]:
            ax.text(x, y, txt, ha='left', va='top', transform=ax.transAxes,
                    fontfamily=F_RETRO, fontsize=FS['sum_body'],
                    fontweight='bold', color=C['ink-dim'])
        y -= 0.035

        for name in ordered_names:
            data = self.results[name]
            is_best = (name == best_name)
            row_col = C['green'] if is_best else data['color']
            ax.add_patch(mpatches.FancyBboxPatch(
                (0.045, y-0.018), 0.020, 0.026,
                boxstyle='square,pad=0', transform=ax.transAxes,
                facecolor=data['color'], edgecolor='none', alpha=0.85))
            ax.text(0.075, y, name,
                    ha='left', va='top', transform=ax.transAxes,
                    fontfamily=F_RETRO, fontsize=FS['sum_body'],
                    fontweight='bold', color=row_col)
            ax.text(0.41, y, f"{data['seek']}",
                    ha='left', va='top', transform=ax.transAxes,
                    fontfamily=F_MONO, fontsize=FS['sum_body'],
                    fontweight='bold' if is_best else 'normal', color=row_col)
            ax.text(0.59, y, f"{data['avg']:.1f}",
                    ha='left', va='top', transform=ax.transAxes,
                    fontfamily=F_MONO, fontsize=FS['sum_body'], color=C['ink'])
            ax.text(0.76, y, f"{100.0 / (data['avg'] + 1):.2f}",
                    ha='left', va='top', transform=ax.transAxes,
                    fontfamily=F_MONO, fontsize=FS['sum_body'], color=C['ink'])
            y -= 0.056

        y = _rule(y)
        best = self.results[best_name]
        ax.add_patch(mpatches.FancyBboxPatch(
            (0.04, 0.055), 0.92, 0.085,
            boxstyle='round,pad=0.01', transform=ax.transAxes,
            facecolor=C['green-bg'], edgecolor=C['green'],
            linewidth=max(1.2, 1.8*S), zorder=3))
        ax.text(0.50, 0.106,
                f'★ BEST: {best_name}',
                ha='center', va='center', transform=ax.transAxes,
                fontfamily=F_RETRO, fontsize=FS['sum_head'],
                fontweight='bold', color=C['green'], zorder=4)
        ax.text(0.50, 0.073,
                f'Seek: {best["seek"]} cyls  ·  Avg: {best["avg"]:.1f} / req',
                ha='center', va='center', transform=ax.transAxes,
                fontfamily=F_MONO, fontsize=FS['sum_body'],
                color=C['ink-mid'], zorder=4)

    # ── Empty state ───────────────────────────────────────────────────────────

    def _draw_empty(self):
        cfgs = [
            ('seek_path',  'Seek Path — All Algorithms',  None),
            ('comparison', 'Total Seek Distance',          None),
            ('fcfs',       'FCFS — Seek Sequence',         C['algo_fcfs']),
            ('sstf',       'SSTF — Seek Sequence',         C['algo_sstf']),
            ('scan',       'SCAN — Seek Sequence',         C['algo_scan']),
            ('cscan',      'C-SCAN — Seek Sequence',       C['algo_cscan']),
        ]
        for key, title, sc in cfgs:
            ax = self.axes[key]
            ax.clear()
            style_ax(ax, title, spine_color=sc or C['ink'])
            ax.text(0.50, 0.50, 'Run Simulation to View',
                    ha='center', va='center', transform=ax.transAxes,
                    fontfamily=F_RETRO, fontsize=FS['widget_lbl'],
                    color=C['ink-dim'], alpha=0.50)

    # ══════════════════════════════════════════════════════════════════════════
    #  RUN
    # ══════════════════════════════════════════════════════════════════════════

    def run(self):
        # Manual geometry is already fixed; avoid an extra layout pass that can
        # distort widget alignment and add startup latency.
        plt.show()
        logging.info('Simulator closed')


# ──────────────────────────────────────────────────────────────────────────────
if __name__ == '__main__':
    print('=' * 62)
    print('  DISK SCHEDULING SIMULATOR  —  Bright Retro Theme')
    print(f'  Screen → figure: {FIG_W:.1f}" × {FIG_H:.1f}"  (scale S={S:.2f})')
    print('  Algorithms: FCFS · SSTF · SCAN · C-SCAN')
    print('=' * 62)
    print()
    print('  ROW 1 CONTROLS')
    print('  ▶ RUN      — execute all four algorithms')
    print('  RESET      — restore factory defaults')
    print('  Disk       — total cylinder count  (e.g. 200)')
    print('  Head       — starting head position (e.g. 53)')
    print('  Queue      — comma-separated request list')
    print()
    print('  ROW 2 CONTROLS')
    print('  SCAN DIR   — sweep direction for SCAN / C-SCAN')
    print('  PRESETS    — Classic / Scattered / Clustered / Sequential')
    print()
    print('  If the window does not appear, change matplotlib.use()')
    print('  near the top of the file to: Qt5Agg | Qt6Agg | MacOSX')
    print('=' * 62)
    print()
    try:
        sim = DiskSchedulingSimulator()
        sim.run()
    except Exception as exc:
        logging.critical(f'Fatal: {exc}', exc_info=True)
        print(f'\nFATAL ERROR: {exc}')
        print('See disk_scheduler.log for details.')
