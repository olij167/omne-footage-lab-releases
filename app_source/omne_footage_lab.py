#!/usr/bin/env python3
from __future__ import annotations

import colorsys, copy, hashlib, json, os, platform, queue, re, shutil, subprocess, sys, tempfile, threading, time, uuid, webbrowser, zipfile
import urllib.error, urllib.parse, urllib.request
from dataclasses import dataclass, field
from pathlib import Path
import tkinter as tk
import tkinter.font as tkfont
from tkinter import colorchooser, filedialog, messagebox, simpledialog, ttk

APP = "OmN-e Footage Lab"
VERSION="0.3.2"
WEBSITE_URL = "https://omne.space/"
SUPPORT_URL = "https://omne.space/support"
UPDATE_MANIFEST_URL = "https://omne.space/downloads/footage-lab/update.json"

UI_PROFILE_FILENAME = "ui_profile.json"

DEFAULT_CHROME = {
    "sash_color": "#666a70",
    "panel_edge": "#555a60",
    "preview_bg": "#111214",
    "tooltip_bg": "#fff6cf",
    "tooltip_fg": "#161616",
    "tooltip_delay_ms": 420,
}

DEFAULT_LABELS = {
    "source_output": "Source / Output", "camera_folder": "Camera folder", "browse": "Browse", "scan": "Scan",
    "output": "Output", "max_upload": "Max upload MiB", "about_updates": "About / Updates…",
    "inspector": "Inspector", "operation": "Operation", "lossless": "Lossless minimal clips", "glitch_derivative": "Glitch derivative",
    "format_tab": "Format", "glitch_tab": "Glitch", "resolution": "Resolution", "fps": "FPS", "crf": "CRF",
    "max_bitrate": "Max bitrate Mbps", "x264": "x264", "preset": "Preset", "save_preset": "Save Current as Preset…",
    "generation_passes": "Generation passes", "scan_strength": "Scan strength", "motion_interpolation": "Motion interpolation",
    "interpolation_source_fps": "Interpolation source FPS", "echo_frames": "Echo frames", "echo_decay": "Echo decay",
    "afterglow": "Afterglow", "chroma_shift": "Chroma shift", "blur": "Blur", "liquid_warp": "Liquid warp",
    "saturation": "Saturation", "hue_drift": "Hue drift", "apply_folder": "Apply Folder", "apply_selected": "Apply Selected",
    "reset_defaults": "Reset Defaults", "preview": "Preview", "source": "Source", "render_preview": "Render Preview",
    "cancel_preview": "Cancel Preview", "play_pause": "Play / Pause", "start": "Start", "length": "Length",
    "processes": "Processes", "retry": "Retry", "repair_retry": "Repair + Retry", "cancel_running": "Cancel Running",
    "open_output": "Open Output", "diagnostics": "Diagnostics…", "copy_job_log": "Copy Job Log", "open_logs": "Open Logs",
    "visit_site": "Visit omne.space", "support": "Support / Donate", "updates": "Updates", "check_now": "Check Now",
    "download_install": "Download & Install", "check_updates_startup": "Check for updates whenever the app opens",
    "theme": "Theme", "theme_help": "Choose a published or locally saved interface theme.", "customize_theme": "Customize…",
    "quick_use_title": "Quick Use",
    "quick_use_body": "1. Choose folders + Scan.\n2. Pick Lossless or Glitch.\n3. Preview/tune one clip.\n4. Apply Selected or Folder.",
    "enable_tooltips": "Enable explanatory tooltips",
    "show_welcome": "Show this welcome panel on startup", "continue": "Continue",
}

DEFAULT_TOOLTIPS = {
    "source_output": "Choose where the untouched camera files live and where converted derivatives should be written. Source files are never edited in place.",
    "camera_folder": "Folder containing the original camera videos. Use Browse to select it, then Scan so the Preview and Apply Folder controls know which files to process.",
    "browse": "Open a folder picker for this path instead of typing it manually.",
    "scan": "Read the selected camera folder and populate the source list. Scanning does not convert or modify any video.",
    "output": "Destination root for lossless clips, glitch derivatives, metadata and work files. Keep this separate from the raw camera folder.",
    "max_upload": "Hard maximum size for each finished upload file. Lossless mode stream-copies and splits around keyframes; glitch mode renders then splits any rare oversize result without another visual encode.",
    "about_updates": "Open release information, website/support links and the automatic updater. Update checks are read from omne.space.",
    "inspector": "Controls how the selected source or whole folder will be processed. Preview uses the same glitch recipe through a faster proxy.",
    "operation": "Choose whether to preserve the original encoded streams and only clip them, or render a separate artistic glitch derivative.",
    "lossless": "Preserve the camera's encoded video/audio packets. Files under the size limit are copied; larger files are clipped with FFmpeg stream-copy, so there is no new codec generation.",
    "glitch_derivative": "Render a new video using the Format and Glitch controls. The raw camera file remains untouched.",
    "format_tab": "Encoding/output controls used for glitch derivatives. Lossless mode ignores these because it preserves the source streams.",
    "glitch_tab": "Artistic conversion controls. Start with a named preset, then change individual values and preview before committing a folder batch.",
    "resolution": "Output frame size for glitch renders. Smaller sizes strengthen early-digital texture and render faster; Source keeps the camera dimensions.",
    "fps": "Output frame cadence for glitch renders. Lower values can feel more period-correct and make echo/interpolation artifacts more visible.",
    "crf": "x264 quality target for the final stable H.264 bake. Lower numbers retain more detail and create larger files; higher numbers add compression and shrink files.",
    "max_bitrate": "Peak video data rate used to estimate safe clip lengths and cap encoded bandwidth. Lower values can increase compression artifacts and reduce upload size.",
    "x264": "Encoder speed/efficiency tradeoff. Faster settings preview and batch faster; slower settings usually compress the same quality into less data.",
    "preset": "Load a named glitch recipe. Built-in presets remain available; manual recipes can be saved as custom presets for reuse.",
    "save_preset": "Save the current Format + Glitch controls as a reusable custom preset. Folder paths and upload limits are intentionally not stored in visual presets.",
    "generation_passes": "Re-encode through MPEG-4 multiple times before the stable final bake. Each pass builds authentic generation-loss softness, block texture and motion residue.",
    "scan_strength": "Darken alternating horizontal luma rows to exaggerate scan/field texture. Keep moderate if the original scene should remain easy to interpret.",
    "motion_interpolation": "Discard some temporal samples and ask motion compensation to reconstruct them. Its imperfect guesses create smooth liquid deformation around moving objects.",
    "interpolation_source_fps": "Cadence fed into the motion interpolator. Lower values remove more real motion information, creating stronger invented in-between motion and warping.",
    "echo_frames": "Number of recent frames mixed into the present frame. Higher values leave longer visual trails and repetitions behind moving subjects.",
    "echo_decay": "How quickly older echo frames fade. Low values keep only a faint immediate echo; high values make earlier frames remain prominent for longer.",
    "afterglow": "Persistence of bright pixels between frames, similar to slow sensor/display decay. Useful for headlights, reflections, sunsets and luminous motion trails.",
    "chroma_shift": "Offset colour channels horizontally/vertically while keeping luminance readable. Creates camera/circuit-bent colour bleeding without destroying scene structure.",
    "blur": "Apply Gaussian softening after the temporal/colour effects. Small values blend harsh digital edges into a hazy, nostalgic image.",
    "liquid_warp": "Strength of smooth animated displacement maps. Higher values bend the image like moving glass rather than breaking it into random pixel blocks.",
    "saturation": "Colour intensity after the glitch chain. Values above 1 make colours more vivid; values below 1 produce faded or forlorn colour.",
    "hue_drift": "Slowly oscillate hue over time. Small values create subtle unstable camera colour; large values become intentionally psychedelic.",
    "apply_folder": "Queue every scanned source using the current operation and Inspector settings. Jobs run one at a time to avoid CPU/disk contention.",
    "apply_selected": "Queue only the clip currently selected in Preview. Use this to validate a recipe before processing the full camera folder.",
    "reset_defaults": "Restore application folders and Inspector values to factory defaults. Custom presets, converted media, logs and job history are kept.",
    "preview": "Render a short proxy from the selected source using the current glitch recipe. This is for visual tuning; final output uses the Inspector format settings.",
    "source": "Select which scanned camera clip is used for Preview or Apply Selected.",
    "render_preview": "Render the chosen time range through the current glitch recipe and display it here. Preview is intentionally reduced for responsiveness.",
    "cancel_preview": "Stop the active preview FFmpeg process without affecting queued/full conversions.",
    "play_pause": "Pause or resume the in-panel preview animation after a preview has successfully rendered.",
    "start": "Seconds from the beginning of the selected source where the preview test should start. Pick a section containing the kind of motion/light you want to judge.",
    "length": "Duration of the preview test. Short tests are faster; use a few extra seconds when judging echoes, afterglow or interpolation behavior.",
    "processes": "Monitor batch work. Rows show queued, running, completed, failed or cancelled jobs plus the current stage and percentage.",
    "retry": "Queue the selected job again with the exact settings originally assigned to it. Useful for transient failures without changing the recipe.",
    "repair_retry": "Delete only the selected job's recorded derivative outputs, then queue the same job again. Raw source files are never removed.",
    "cancel_running": "Terminate the currently active batch FFmpeg process. Already completed jobs and source files are left intact.",
    "open_output": "Open the active output folder in the system file manager so you can inspect completed derivatives.",
    "diagnostics": "Open a copyable report containing versions, paths, current Inspector values, job states and recent FFmpeg/session logs for debugging.",
    "copy_job_log": "Copy the selected job's most recent FFmpeg log to the clipboard. If no job log is selected, the latest preview log or diagnostics are copied instead.",
    "open_logs": "Open the persistent log folder. Use these files when a conversion fails before the UI can explain the FFmpeg error clearly.",
    "visit_site": "Open omne.space in your default browser.",
    "support": "Open the stable omne.space support page; the underlying donation provider can change without requiring a new application build.",
    "updates": "Update status for this installation. The app checks a signed-by-hash release manifest hosted at omne.space.",
    "check_now": "Immediately fetch the current update manifest from omne.space and compare its version with this installation.",
    "download_install": "Download the platform package from omne.space, verify its SHA-256 hash, install it, and then offer to restart the app.",
    "check_updates_startup": "When enabled, perform a non-blocking update check shortly after every launch. Conversion still works when the update service is offline.",
    "enable_tooltips": "Show concise utility help when hovering interface controls. Turn this off if you already know the workflow and prefer a quieter interface.",
    "quick_use": "Four-step reminder of the normal workflow. The owner can edit this wording in the Labels section of the Customiser.",
    "customize_theme": "Open the live Theme Studio. Every colour and sizing adjustment is applied to the running interface immediately; save the result as a local theme when you want to keep it.",
    "show_welcome": "Show the compact website/support/update panel whenever Footage Lab starts.",
    "continue": "Close the welcome/update panel and return to Footage Lab.",
    "resize_outer": "Drag the visible horizontal handle to rebalance Source/Output, Workspace and Processes. The handle is constrained so fixed-height toolbars cannot be stretched into empty space.",
    "resize_workspace": "Drag the vertical handle to give more width to Inspector or Preview. Minimum widths keep both sides usable.",
    "resize_inspector": "Drag the horizontal handle to rebalance the operation summary and Inspector controls. The summary region is capped near its actual content height.",
    "resize_preview": "Drag the horizontal handle to rebalance Preview controls and the video area. The controls region is capped near its actual content height.",
}

def _merge_ui_profile(base, incoming):
    result=copy.deepcopy(base)
    if isinstance(incoming,dict):
        for key,value in incoming.items():
            if isinstance(value,dict) and isinstance(result.get(key),dict):result[key].update(value)
            else:result[key]=value
    return result

def load_packaged_ui_profile():
    path=Path(os.environ.get("OMNE_FOOTAGE_LAB_UI_PROFILE",str(app_base_dir()/UI_PROFILE_FILENAME)))
    try:
        if path.exists():return validate_ui_profile(json.loads(path.read_text(encoding="utf-8")))
    except Exception as error:
        print(f"UI profile validation failed; using defaults: {error}",file=sys.stderr)
    return profile_defaults()

class ToolTip:
    def __init__(self,widget,text,bg="#fff6cf",fg="#161616",delay=420):
        self.widget=widget; self.text=str(text or ""); self.bg=bg; self.fg=fg; self.delay=max(50,int(delay)); self.after_id=None; self.win=None; self.enabled=True
        widget.bind("<Enter>",self._enter,add="+"); widget.bind("<Leave>",self._leave,add="+"); widget.bind("<ButtonPress>",self._leave,add="+")
    def set_enabled(self,enabled):
        self.enabled=bool(enabled)
        if not self.enabled:
            self._cancel(); self._hide()
    def _enter(self,_e=None):
        if not self.enabled:return
        self._cancel(); self.after_id=self.widget.after(self.delay,self._show)
    def _leave(self,_e=None):
        self._cancel(); self._hide()
    def _cancel(self):
        if self.after_id:
            try:self.widget.after_cancel(self.after_id)
            except Exception:pass
            self.after_id=None
    def _show(self):
        if not self.enabled or not self.text or self.win:return
        try:
            x=self.widget.winfo_rootx()+18; y=self.widget.winfo_rooty()+self.widget.winfo_height()+8
            self.win=tk.Toplevel(self.widget); self.win.wm_overrideredirect(True); self.win.wm_geometry(f"+{x}+{y}")
            label=tk.Label(self.win,text=self.text,justify="left",wraplength=_ACTIVE_PROFILE.get("chrome",DEFAULT_CHROME).get("tooltip_wrap_px",390),bg=self.bg,fg=self.fg,relief="solid",bd=1,padx=8,pady=6,font=(_ACTIVE_PROFILE.get("chrome",DEFAULT_CHROME).get("font_family","TkDefaultFont"),_ACTIVE_PROFILE.get("chrome",DEFAULT_CHROME).get("tooltip_font_size",9)))
            label.pack()
            self.win.update_idletasks()
            x=max(0,min(x,self.widget.winfo_screenwidth()-self.win.winfo_reqwidth()-8))
            y=max(0,min(y,self.widget.winfo_screenheight()-self.win.winfo_reqheight()-8))
            self.win.wm_geometry(f"+{x}+{y}")
        except Exception:self.win=None
    def _hide(self):
        if self.win:
            try:self.win.destroy()
            except Exception:pass
            self.win=None

class ResizablePane(tk.PanedWindow):
    """PanedWindow with hard drag limits.

    Tk's native paned-window binding lets the pointer temporarily drag a sash
    beyond the useful range and only gets corrected later by application
    layout code.  This class owns the sash drag itself so the divider stops at
    its bound immediately, which removes the visible over-drag/snap-back.
    """
    def __init__(self,master,orient,chrome,**kw):
        vertical=orient in (tk.VERTICAL,"vertical")
        super().__init__(master,orient=orient,opaqueresize=True,showhandle=True,
                         handlesize=chrome.get("handle_size",9),handlepad=chrome.get("handle_offset",18),
                         sashwidth=chrome.get("sash_width",7),sashrelief=tk.RAISED,
                         bd=0,relief=tk.FLAT,bg=chrome.get("sash_color","#666a70"),
                         sashcursor="sb_v_double_arrow" if vertical else "sb_h_double_arrow",**kw)
        self._bounds_provider=None
        self._drag_index=None
        self._drag_offset=0
        self.bind("<ButtonPress-1>",self._begin_bounded_drag,add="+")
        self.bind("<B1-Motion>",self._bounded_drag,add="+")
        self.bind("<ButtonRelease-1>",self._end_bounded_drag,add="+")
    def add(self,child,**kw):
        kw.pop("weight",None); kw.setdefault("stretch","always"); return super().add(child,**kw)
    def sashpos(self,index,newpos=None):
        x,y=self.sash_coord(index)
        if newpos is None:return y if str(self.cget("orient"))=="vertical" else x
        if self._bounds_provider:
            try:
                lo,hi=self._bounds_provider(index)
                newpos=max(int(lo),min(int(hi),int(newpos)))
            except Exception:pass
        if str(self.cget("orient"))=="vertical":self.sash_place(index,x,int(newpos))
        else:self.sash_place(index,int(newpos),y)
        return int(newpos)
    def set_bounds_provider(self,provider):
        self._bounds_provider=provider
    def _bounds(self,index):
        axis=self.winfo_height() if str(self.cget("orient"))=="vertical" else self.winfo_width()
        try:
            lo,hi=self._bounds_provider(index) if self._bounds_provider else (0,axis)
            lo=int(lo);hi=int(hi)
        except Exception:lo,hi=0,axis
        if hi<lo:hi=lo
        return lo,hi
    def _begin_bounded_drag(self,event):
        try:ident=self.identify(event.x,event.y)
        except tk.TclError:return
        if not ident:return
        try:index=int(ident[0]); kind=str(ident[1])
        except Exception:return
        if kind not in {"sash","handle"}:return
        self._drag_index=index
        coord=event.y if str(self.cget("orient"))=="vertical" else event.x
        self._drag_offset=coord-self.sashpos(index)
        return "break"
    def _bounded_drag(self,event):
        if self._drag_index is None:return
        coord=event.y if str(self.cget("orient"))=="vertical" else event.x
        lo,hi=self._bounds(self._drag_index)
        desired=max(lo,min(hi,int(coord-self._drag_offset)))
        self.sashpos(self._drag_index,desired)
        return "break"
    def _end_bounded_drag(self,event):
        if self._drag_index is None:return
        index=self._drag_index;self._drag_index=None
        lo,hi=self._bounds(index);self.sashpos(index,max(lo,min(hi,self.sashpos(index))))
        try:self.event_generate("<<OmneSashChanged>>",when="tail")
        except tk.TclError:pass
        return "break"

class CollapsibleSection(ttk.Frame):
    """Compact input/tool section that expands without internal scrolling."""
    def __init__(self,parent,title,*,expanded=True,on_toggle=None):
        super().__init__(parent)
        self.title=title;self.expanded=bool(expanded);self.on_toggle=on_toggle
        self.columnconfigure(0,weight=1)
        self.header=ttk.Button(self,style="Collapse.TButton",command=self.toggle)
        self.header.grid(row=0,column=0,sticky="ew")
        self.body=ttk.Frame(self,padding=(4,4,4,5));self.body.grid(row=1,column=0,sticky="ew")
        self._paint()
    def _paint(self):
        self.header.configure(text=("▾ " if self.expanded else "▸ ")+self.title)
        if self.expanded:self.body.grid()
        else:self.body.grid_remove()
    def set_title(self,title):self.title=str(title);self._paint()
    def set_expanded(self,value,notify=False):
        value=bool(value)
        if value==self.expanded:return
        self.expanded=value;self._paint()
        if notify and self.on_toggle:self.on_toggle(self.expanded)
    def toggle(self):self.set_expanded(not self.expanded,notify=True)

class SearchableFontCombobox(ttk.Combobox):
    """Editable font selector that filters installed families as the user types."""
    def __init__(self,parent,**kw):
        try:families=sorted(set(tkfont.families(parent)))
        except Exception:families=[]
        self._all_fonts=families
        kw.setdefault("values",families);kw.setdefault("state","normal")
        super().__init__(parent,**kw)
        self.bind("<KeyRelease>",self._filter_fonts,add="+")
        self.bind("<FocusIn>",self._restore_fonts,add="+")
    def _restore_fonts(self,event=None):
        if not self.get().strip():self.configure(values=self._all_fonts)
    def _filter_fonts(self,event=None):
        if event is not None and getattr(event,"keysym","") in {"Up","Down","Left","Right","Return","Escape","Tab"}:return
        needle=self.get().casefold().strip()
        values=self._all_fonts if not needle else [f for f in self._all_fonts if needle in f.casefold()]
        self.configure(values=values[:400])

class AdvancedColorPicker(tk.Toplevel):
    """HSV/RGB/HEX colour picker with wheel and best-effort desktop eyedropper.

    The picker deliberately has no dependency on the public App instance so the
    same UI is available in the owner Customiser.  All visible wording and hover
    help come from the active UI profile, keeping the picker authorable too.
    """
    SIZE=220
    def __init__(self,parent,initial="#FFFFFF",title="Choose colour"):
        super().__init__(parent);self.withdraw();self.transient(parent);self.title(title);self.resizable(False,False)
        self.result=None;self._loading=False;self._wheel_photo=None;self._wheel_img=None;self._wheel_value_cached=None;self._regen_after=None;self._tips=[]
        self.h=tk.DoubleVar(value=0);self.s=tk.DoubleVar(value=0);self.v=tk.DoubleVar(value=1)
        self.r=tk.IntVar(value=255);self.g=tk.IntVar(value=255);self.b=tk.IntVar(value=255);self.hex=tk.StringVar(value="#FFFFFF")
        outer=ttk.Frame(self,padding=10);outer.pack(fill="both",expand=True)
        left=ttk.Frame(outer);left.grid(row=0,column=0,sticky="n")
        right=ttk.Frame(outer);right.grid(row=0,column=1,sticky="nsew",padx=(12,0));right.columnconfigure(1,weight=1)
        self.wheel=tk.Canvas(left,width=self.SIZE,height=self.SIZE,highlightthickness=1,highlightbackground="#777")
        self.wheel.pack();self.wheel.bind("<Button-1>",self._wheel_pick);self.wheel.bind("<B1-Motion>",self._wheel_pick);self._tip(self.wheel,"color_picker")
        self.swatch=tk.Canvas(left,width=self.SIZE,height=32,highlightthickness=1,highlightbackground="#777");self.swatch.pack(pady=(7,0));self._tip(self.swatch,"color_picker")
        ttk.Label(right,text=self._label("color_hsv","HSV"),style="Title.TLabel").grid(row=0,column=0,columnspan=2,sticky="w",pady=(0,4))
        self._spin_row(right,1,"color_hue","Hue °",self.h,0,359,1,self._from_hsv)
        self._spin_row(right,2,"color_saturation","Saturation %",self.s,0,100,1,self._from_hsv)
        self._spin_row(right,3,"color_value","Value %",self.v,0,100,1,self._from_hsv)
        ttk.Label(right,text=self._label("color_rgb","RGB"),style="Title.TLabel").grid(row=4,column=0,columnspan=2,sticky="w",pady=(9,4))
        self._spin_row(right,5,"color_red","Red",self.r,0,255,1,self._from_rgb)
        self._spin_row(right,6,"color_green","Green",self.g,0,255,1,self._from_rgb)
        self._spin_row(right,7,"color_blue","Blue",self.b,0,255,1,self._from_rgb)
        hl=ttk.Label(right,text=self._label("color_hex","HEX"));hl.grid(row=8,column=0,sticky="w",pady=(8,2));self._tip(hl,"color_picker")
        he=ttk.Entry(right,textvariable=self.hex,width=12);he.grid(row=8,column=1,sticky="ew",pady=(8,2));he.bind("<Return>",lambda e:self._from_hex());he.bind("<FocusOut>",lambda e:self._from_hex());self._tip(he,"color_picker")
        self.status=tk.StringVar(value=self._label("color_status","Colour wheel · HSV · RGB · HEX"))
        eye=ttk.Button(right,text=self._label("color_eyedropper","Eyedropper · sample screen in 2s"),command=self._eyedropper);eye.grid(row=9,column=0,columnspan=2,sticky="ew",pady=(9,3));self._tip(eye,"color_eyedropper")
        ttk.Label(right,textvariable=self.status,style="Muted.TLabel",wraplength=250,justify="left").grid(row=10,column=0,columnspan=2,sticky="ew")
        actions=ttk.Frame(outer);actions.grid(row=1,column=0,columnspan=2,sticky="e",pady=(10,0))
        ttk.Button(actions,text=self._label("color_cancel","Cancel"),command=self._cancel).pack(side="right")
        ttk.Button(actions,text=self._label("color_use","Use Colour"),command=self._ok).pack(side="right",padx=(0,6))
        self.protocol("WM_DELETE_WINDOW",self._cancel);self.bind("<Escape>",lambda _e:self._cancel())
        self._set_hex(initial if re.fullmatch(r"#[0-9a-fA-F]{6}",str(initial)) else "#FFFFFF")
        self.update_idletasks();self.geometry(f"+{max(0,parent.winfo_rootx()+40)}+{max(0,parent.winfo_rooty()+40)}");self.deiconify();self.grab_set()
    def _label(self,key,default):
        try:return str(_ACTIVE_PROFILE.get("labels",{}).get(key,DEFAULT_LABELS.get(key,default)))
        except Exception:return str(DEFAULT_LABELS.get(key,default))
    def _tip(self,widget,key):
        try:
            text=str(_ACTIVE_PROFILE.get("tooltips",{}).get(key,DEFAULT_TOOLTIPS.get(key,"")))
            chrome=_ACTIVE_PROFILE.get("chrome",DEFAULT_CHROME)
            if text:self._tips.append(ToolTip(widget,text,chrome.get("tooltip_bg","#fff6cf"),chrome.get("tooltip_fg","#161616"),chrome.get("tooltip_delay_ms",420)))
        except Exception:pass
        return widget
    @classmethod
    def choose(cls,parent,initial="#FFFFFF",title="Choose colour"):
        dlg=cls(parent,initial,title);parent.wait_window(dlg);result=dlg.result
        try:
            if parent.winfo_exists():parent.grab_set()
        except Exception:pass
        return result
    def _spin_row(self,parent,row,key,default,var,a,b,inc,callback):
        lab=ttk.Label(parent,text=self._label(key,default));lab.grid(row=row,column=0,sticky="w",pady=2);self._tip(lab,"color_picker")
        sp=ttk.Spinbox(parent,from_=a,to=b,increment=inc,textvariable=var,width=8,command=callback);sp.grid(row=row,column=1,sticky="ew",pady=2);sp.bind("<Return>",lambda e:callback());sp.bind("<FocusOut>",lambda e:callback());self._tip(sp,"color_picker")
    def _set_hex(self,value):
        value=str(value).upper();r=int(value[1:3],16);g=int(value[3:5],16);b=int(value[5:7],16)
        h,s,v=colorsys.rgb_to_hsv(r/255,g/255,b/255);self._loading=True
        self.r.set(r);self.g.set(g);self.b.set(b);self.h.set(round(h*360)%360);self.s.set(round(s*100));self.v.set(round(v*100));self.hex.set(value);self._loading=False;self._paint()
    def _from_rgb(self):
        if self._loading:return
        try:r=max(0,min(255,int(self.r.get())));g=max(0,min(255,int(self.g.get())));b=max(0,min(255,int(self.b.get())))
        except Exception:return
        self._set_hex(f"#{r:02X}{g:02X}{b:02X}")
    def _from_hsv(self):
        if self._loading:return
        try:h=(float(self.h.get())%360)/360;s=max(0,min(100,float(self.s.get())))/100;v=max(0,min(100,float(self.v.get())))/100
        except Exception:return
        r,g,b=colorsys.hsv_to_rgb(h,s,v);self._set_hex(f"#{round(r*255):02X}{round(g*255):02X}{round(b*255):02X}")
    def _from_hex(self):
        value=str(self.hex.get()).strip()
        if not value.startswith("#"):value="#"+value
        if re.fullmatch(r"#[0-9a-fA-F]{6}",value):self._set_hex(value)
        else:self.status.set(self._label("color_invalid_hex","HEX must contain six hexadecimal digits."))
    def _wheel_pick(self,event):
        cx=cy=self.SIZE/2;dx=event.x-cx;dy=event.y-cy;radius=self.SIZE/2-3;dist=(dx*dx+dy*dy)**0.5
        s=min(1,dist/radius)
        import math as _math
        hue=(_math.degrees(_math.atan2(dy,dx))+360)%360
        self._loading=True;self.h.set(round(hue));self.s.set(round(s*100));self._loading=False;self._from_hsv()
    def _paint(self):
        try:value=max(0,min(1,float(self.v.get())/100))
        except Exception:value=1
        if Image and ImageTk:
            import math as _math
            size=self.SIZE;rad=size/2-3;wheel_value=round(value,3)
            if self._wheel_photo is None or self._wheel_value_cached!=wheel_value:
                im=Image.new("RGB",(size,size),(45,45,45));pix=im.load()
                for y in range(size):
                    dy=y-size/2
                    for x in range(size):
                        dx=x-size/2;d=(dx*dx+dy*dy)**0.5
                        if d<=rad:
                            hue=(_math.degrees(_math.atan2(dy,dx))+360)%360/360;sat=min(1,d/rad);rr,gg,bb=colorsys.hsv_to_rgb(hue,sat,value);pix[x,y]=(round(rr*255),round(gg*255),round(bb*255))
                self._wheel_img=im;self._wheel_photo=ImageTk.PhotoImage(im,master=self);self._wheel_value_cached=wheel_value;self.wheel.delete("all");self.wheel.create_image(0,0,anchor="nw",image=self._wheel_photo)
            else:self.wheel.delete("marker")
            hue=float(self.h.get())%360;sat=float(self.s.get())/100
            x=size/2+_math.cos(_math.radians(hue))*sat*rad;y=size/2+_math.sin(_math.radians(hue))*sat*rad
            self.wheel.create_oval(x-6,y-6,x+6,y+6,outline="black",tags="marker");self.wheel.create_oval(x-5,y-5,x+5,y+5,outline="white",width=2,tags="marker")
        colour=self.hex.get();self.swatch.delete("all");self.swatch.create_rectangle(0,0,self.SIZE,32,fill=colour,outline="")
    def _eyedropper(self):
        if not ImageGrab:
            self.status.set(self._label("color_capture_required","Screen sampling requires Pillow/ImageGrab on this platform."));return
        self.status.set(self._label("color_sampling","Move the pointer over any pixel on the desktop · sampling in 2 seconds…"))
        try:self.attributes("-alpha",0.18)
        except Exception:pass
        self.after(2000,self._sample_pointer)
    def _sample_pointer(self):
        try:
            x=self.winfo_pointerx();y=self.winfo_pointery()
            try:img=ImageGrab.grab(all_screens=True)
            except TypeError:img=ImageGrab.grab()
            w,h=img.size
            if not (0<=x<w and 0<=y<h):raise RuntimeError("Pointer is outside the captured desktop bounds")
            px=img.convert("RGB").getpixel((x,y));self._set_hex(f"#{px[0]:02X}{px[1]:02X}{px[2]:02X}");self.status.set(self._label("color_sampled","Sampled screen pixel at {x}, {y}.").format(x=x,y=y))
        except Exception as e:self.status.set(self._label("color_eyedropper_unavailable","Screen eyedropper unavailable: {error}").format(error=e))
        finally:
            try:self.attributes("-alpha",1.0)
            except Exception:pass
    def _ok(self):
        self.result=self.hex.get().upper()
        try:self.grab_release()
        except tk.TclError:pass
        self.destroy()
    def _cancel(self):
        self.result=None
        try:self.grab_release()
        except tk.TclError:pass
        self.destroy()

def app_base_dir():
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent

def find_tool(name):
    exe=name+".exe" if os.name=="nt" else name
    bases=[app_base_dir()]
    if getattr(sys,"_MEIPASS",None):bases.insert(0,Path(sys._MEIPASS))
    for base in bases:
        for candidate in (base/"tools"/exe,base/exe):
            if candidate.exists():return str(candidate)
    return shutil.which(name)

def user_config_dir():
    if os.environ.get("OMNE_FOOTAGE_LAB_SANDBOX"):return Path(os.environ["OMNE_FOOTAGE_LAB_SANDBOX"])/"config"
    if os.name=="nt":
        return Path(os.environ.get("APPDATA", Path.home()/"AppData"/"Roaming"))/"OmN-e Footage Lab"
    if sys.platform=="darwin":
        return Path.home()/"Library"/"Application Support"/"OmN-e Footage Lab"
    return Path(os.environ.get("XDG_CONFIG_HOME",Path.home()/".config"))/"omne-footage-lab"

def user_state_dir():
    if os.environ.get("OMNE_FOOTAGE_LAB_SANDBOX"):return Path(os.environ["OMNE_FOOTAGE_LAB_SANDBOX"])/"state"
    if os.name=="nt":
        return Path(os.environ.get("LOCALAPPDATA", Path.home()/"AppData"/"Local"))/"OmN-e Footage Lab"
    if sys.platform=="darwin":
        return Path.home()/"Library"/"Logs"/"OmN-e Footage Lab"
    return Path(os.environ.get("XDG_STATE_HOME",Path.home()/".local"/"state"))/"omne-footage-lab"

def user_theme_path():
    return user_config_dir()/"user_themes.json"


def load_user_themes():
    path=user_theme_path()
    try:
        data=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {}
        if not isinstance(data,dict):return {}
        cleaned={}
        for name,chrome in data.items():
            if not isinstance(name,str) or not name.strip() or not isinstance(chrome,dict):continue
            merged={**copy.deepcopy(DEFAULT_CHROME),**chrome}
            try:
                validate_ui_profile(_merge_ui_profile(profile_defaults(),{"themes":{"_local":merged},"published_themes":["_local"],"default_theme":"_local"}))
            except Exception:continue
            cleaned[name]=merged
        return cleaned
    except Exception:return {}


def save_user_themes(themes):
    path=user_theme_path(); path.parent.mkdir(parents=True,exist_ok=True)
    temp=path.with_name(path.name+".tmp")
    temp.write_text(json.dumps(themes,indent=2,ensure_ascii=False,sort_keys=True)+"\n",encoding="utf-8")
    os.replace(temp,path)


def open_path(path):
    path=str(path)
    if os.name=="nt":
        os.startfile(path)
    elif sys.platform=="darwin":
        subprocess.Popen(["open",path])
    else:
        subprocess.Popen(["xdg-open",path])

def default_source_path():
    preferred=Path.home()/"Documents"/"Footage"/"DCIM"/"100SANYO"
    if preferred.exists():return str(preferred)
    media=(Path.home()/"Movies") if sys.platform=="darwin" else (Path.home()/"Videos")
    return str(media if media.exists() else Path.home())

def version_key(value):
    return tuple(int(x) for x in re.findall(r"\d+",str(value))[:4]) or (0,)

def update_platform_key():
    machine=(platform.machine() or "").lower()
    if os.name=="nt":
        return "windows-arm64" if machine in {"arm64","aarch64"} else "windows-x64"
    if sys.platform=="darwin":
        return "macos-arm64" if machine in {"arm64","aarch64"} else "macos-x64"
    if sys.platform.startswith("linux"):return "linux"
    return sys.platform

def update_platform_fallback(key):
    return {
        "windows-x64":"windows",
        "windows-arm64":"windows",
        "macos-arm64":"macos",
        "macos-x64":"macos",
    }.get(key)

FFMPEG_BIN=find_tool("ffmpeg")
FFPROBE_BIN=find_tool("ffprobe")
DEFAULT_SOURCE = default_source_path()
EXTS = {".mp4",".mov",".m4v",".mkv",".avi",".mts",".m2ts",".webm"}

DEFAULT_UI = dict(
    source=DEFAULT_SOURCE,
    output=DEFAULT_SOURCE+"_OMNE_FOOTAGE_LAB",
    max_mib=48.0,
    mode="lossless",
    preset="Manual",
    resolution="640x360",
    fps=29.97,
    crf=18,
    bitrate=3.0,
    x264="veryfast",
    generation=0,
    scan=0.0,
    interp=False,
    interp_fps=12.0,
    echo=1,
    decay=0.30,
    glow=0.0,
    chroma=0.0,
    blur=0.0,
    warp=0.0,
    sat=1.0,
    hue=0.0,
    preview_start=0.0,
    preview_length=4.0,
    preview_source="",
    show_startup=True,
    check_updates=True,
    enable_tooltips=True,
)

PRESETS = {
    "Manual": {},
    "Generation Loss": dict(generation=3, scan=0, interp=0, echo=1, decay=.3, glow=0, chroma=0, blur=0, warp=0, sat=1, hue=0),
    "Compact Scan": dict(generation=0, scan=.55, interp=0, echo=1, decay=.3, glow=0, chroma=2, blur=.12, warp=0, sat=1.06, hue=.4),
    "Liquid Interp": dict(generation=0, scan=0, interp=1, interp_fps=10, echo=3, decay=.30, glow=0, chroma=0, blur=.35, warp=4, sat=1.06, hue=0),
    "CCD Afterglow": dict(generation=0, scan=0, interp=0, echo=5, decay=.46, glow=.96, chroma=1, blur=.22, warp=0, sat=1.12, hue=.4),
    "Chroma Bleed": dict(generation=0, scan=0, interp=0, echo=2, decay=.14, glow=0, chroma=4, blur=.18, warp=0, sat=1.18, hue=1.4),
    "River Memory": dict(generation=1, scan=0, interp=1, interp_fps=12, echo=4, decay=.42, glow=.90, chroma=2, blur=.42, warp=6, sat=1.08, hue=.8),
}

def safe(s):
    s = "".join(c if c.isalnum() or c in "._-" else "_" for c in s)
    while "__" in s: s = s.replace("__","_")
    return s.strip("_") or "video"

def sid(p): return hashlib.sha256(str(p.resolve()).encode()).hexdigest()[:8]

def rate(s):
    try:
        a,b=s.split("/",1); return float(a)/float(b)
    except:
        try: return float(s)
        except: return 0.0

# All application-owned presentation lives in ui_profile.json. Native file
# pickers/window frames and unmodified tool diagnostics belong to the OS/tools.
try:
    import PIL
    from PIL import Image, ImageTk, ImageOps, ImageGrab
except ImportError:
    PIL = Image = ImageTk = ImageOps = ImageGrab = None

def _pil_resample_filter(name):
    """Return the modern Pillow resampling enum, with an old-Pillow fallback.

    Pillow added Image.Resampling in 9.1. Older distro Pillow packages expose
    the same filters directly on Image. New Pillow therefore never uses a
    deprecated constant, while older installations remain able to render the
    preview instead of crashing during resize.
    """
    if Image is None:
        return None
    enum = getattr(Image, "Resampling", None)
    if enum is not None and hasattr(enum, name):
        return getattr(enum, name)
    return getattr(Image, name, None)

_PIL_BILINEAR = _pil_resample_filter("BILINEAR")
_PIL_RESAMPLE_API = (
    "Image.Resampling.BILINEAR"
    if Image is not None and getattr(Image, "Resampling", None) is not None
    else "Image.BILINEAR compatibility fallback"
)
import math
import string
from collections import OrderedDict

DEFAULT_IDENTITY = {
    "app_name": "OmN-e Footage Lab",
    "website_url": "https://omne.space/",
    "support_url": "https://omne.space/support",
}
DEFAULT_CHROME.update({
    "background": "#160F1F", "panel_bg": "#21162C", "foreground": "#EEE8F5", "muted_fg": "#A99AB7",
    "field_bg": "#2A1B38", "field_fg": "#F4EEFA",
    "button_bg": "#332144", "button_fg": "#F7F0FF",
    "active_bg": "#4A2D63", "active_fg": "#FFF4C2",
    "selection_bg": "#6F4C8E", "selection_fg": "#FFFFFF",
    "disabled_fg": "#7E708D", "accent": "#FFD75A", "secondary_accent": "#C9A7FF",
    "tab_bg": "#291B37", "tab_selected_bg": "#3B2850",
    "scrollbar_bg": "#6D567E", "scrollbar_trough": "#21162C",
    "scale_bg": "#21162C", "scale_trough": "#4A365A",
    "preview_bg": "#0E0914", "preview_fg": "#DCCAFF",
    "success_fg": "#6FD47A", "warning_fg": "#FFAA45", "failure_fg": "#FF4F87", "running_fg": "#C9A7FF",
    "sash_color": "#6F577F", "panel_edge": "#4C365B",
    "tooltip_bg": "#2A1B38", "tooltip_fg": "#F4EFFF", "tooltip_delay_ms": 360,
    "font_family": "TkDefaultFont", "font_size": 10,
    "heading_size": 12, "welcome_size": 18,
    "mono_font": "TkFixedFont", "mono_size": 9,
    "tooltip_font_size": 9, "tooltip_wrap_px": 390,
    "button_pad_x": 8, "button_pad_y": 5, "panel_padding": 8,
    "border_width": 1, "row_height": 25,
    "sash_width": 7, "handle_size": 10, "handle_offset": 18,
    "slider_length": 175, "scrollbar_width": 13,
})
DEFAULT_LABELS.update({
    "browse_source": "Browse", "browse_output": "Browse",
    "app_title": "{app} {version}", "welcome_title": "{app} · Welcome",
    "welcome_heading": "{app}", "welcome_version": "Prototype release v{version}",
    "welcome_description": "Prepare camera footage for OmN-e Waves, preserve upload-safe lossless clips, and build restrained glitch-art conversion recipes.",
    "format_help": "Glitch outputs only. Lossless mode preserves the camera streams.",
    "preset_help": "Custom presets are saved locally.",
    "preview_help": "Fast proxy for tuning; final output uses the Inspector format.",
    "preview_empty": "Render a short test clip", "stage_result": "Stage / Result",
    "status": "Status", "progress": "Progress", "copy_all": "Copy All",
    "refresh": "Refresh", "open_logs_folder": "Open Logs Folder",
    "diagnostics_title": "{app} Diagnostics", "preset_save_title": "Save Custom Preset",
    "preset_name_prompt": "Preset name:", "preview_fit": "Entire frame · fit to panel",
    "apply_folder_count": "{label} ({count})",
    "state.queued": "queued", "state.running": "running", "state.completed": "completed",
    "state.failed": "failed", "state.cancelled": "cancelled", "state.interrupted": "interrupted",
})
for _name in PRESETS:
    DEFAULT_LABELS["preset." + _name] = _name
DEFAULT_LABELS.update({
    "theme_studio_theme":"Theme", "theme_studio_save":"Save as New Theme…", "theme_studio_revert":"Revert",
    "theme_studio_palette":"Palette", "theme_studio_sizing":"Sizing & density", "theme_pick_title":"Choose ",
    "theme_name_prompt":"Theme name:", "theme_override_builtin":"That is an approved built-in theme. Save a local theme with the same name and override it only on this computer?",
    "theme_saved":"Saved local theme: {name}", "theme_studio_note":"Changes update the running interface immediately. Saved themes stay on this computer and do not change the owner's approved public theme library.",
    "close":"Close", "theme_studio_close":"Close",
    "color_hsv":"HSV", "color_hue":"Hue °", "color_saturation":"Saturation %", "color_value":"Value %",
    "color_rgb":"RGB", "color_red":"Red", "color_green":"Green", "color_blue":"Blue", "color_hex":"HEX",
    "color_eyedropper":"Eyedropper · sample screen in 2s", "color_cancel":"Cancel", "color_use":"Use Colour",
    "color_status":"Colour wheel · HSV · RGB · HEX",
    "color_invalid_hex":"HEX must contain six hexadecimal digits.",
    "color_capture_required":"Screen sampling requires Pillow/ImageGrab on this platform.",
    "color_sampling":"Move the pointer over any pixel on the desktop · sampling in 2 seconds…",
    "color_sampled":"Sampled screen pixel at {x}, {y}.",
    "color_eyedropper_unavailable":"Screen eyedropper unavailable: {error}",
    "theme_override_local":"A personal theme with this name already exists. Replace it?",
})
DEFAULT_TOOLTIPS.update({
    "browse_source": "Select the camera/source folder. Nothing is converted until you queue a job.",
    "browse_output": "Choose a separate destination for clips and effect renders. Do not choose the raw camera folder.",
    "preview": "The full preview frame is centred and scaled to fit this panel, including portrait footage. Drag the visible borders to give it more space. Preview rendering uses a reduced proxy; resizing this panel does not rerender the video.",
    "updates": "Fetch the release manifest over HTTPS and compare versions. SHA-256 checks download integrity; it is not a digital signature or proof against a compromised publisher.",
    "scroll_vertical": "Scroll within this section to reach controls below the visible area. The other sections do not move.",
    "resize_outer": "Drag the visible divider to rebalance the workspace and process monitor. The divider stops at its useful limits while you drag, so neither area can be pushed beyond its valid range.",
    "resize_inspector": "Operation is now collapsible rather than resizable. Use its chevron to hide or restore the compact processing summary; Format and Glitch scroll vertically only when required.",
    "resize_preview": "Preview controls are collapsible rather than resizable. The image automatically uses the remaining area and always contains the entire frame without internal scrolling or cropping.",
    "copy_all": "Copy the entire visible diagnostics report to the clipboard for troubleshooting. Review file paths and other details before sharing.",
    "refresh": "Rebuild the diagnostics text from the current job states and logs.",
    "open_logs_folder": "Open the persistent application log folder in the file manager.",
})
DEFAULT_TOOLTIPS.update({
    "preview_visual": DEFAULT_TOOLTIPS["preview"],
    "preview_heading": DEFAULT_TOOLTIPS["preview"],
    "preview_controls": DEFAULT_TOOLTIPS["preview"],
    "preview_progress": "Completion of the short preview render and display-frame preparation. This does not represent the full-folder batch.",
    "preview_status": "Current preview stage or result. Long messages wrap to the available width; no horizontal scrolling is required.",
    "scan_status": "Number and combined on-disk size of the videos found in the last folder scan.",
    "operation_summary": "Summary of the current processing mode. Lossless clipping preserves encoded packets; effect rendering uses the selected recipe.",
    "inspector_tabs": "Switch between output-format controls and artistic effects. Each tab remembers its own scroll position.",
    "preset_help": "Your saved visual recipes stay on this computer and are preserved through application updates.",
    "queue_status": "Counts of running, queued, completed and failed jobs in this session and restored history.",
    "update_status": DEFAULT_TOOLTIPS["updates"],
    "release_notes": "Changes supplied by the publisher for the available application release.",
    "welcome_heading": "Application name set by the publisher. Use the links below for the project website and support page.",
    "welcome_version": "Version of the application code currently running, not a queued or merely downloaded update.",
    "welcome_description": "Overview of the local footage workflow. The application does not upload your camera files automatically.",
    "diagnostics_text": "Read or copy the diagnostic report. Raw FFmpeg messages are kept unchanged so errors can be diagnosed accurately.",
})
DEFAULT_TOOLTIPS.update({
    "theme_studio_theme":"Choose the approved or locally saved theme used as the starting point for live editing. Selecting a base does not overwrite it.",
    "theme_studio_save":"Save the current live chrome as a personal theme on this computer. Personal themes are not added to the publisher's approved theme set.",
    "theme_studio_revert":"Discard the current unsaved adjustments and reload the selected starting theme.",
    "theme_palette_control":"Sets one semantic interface colour. Click the swatch for the colour wheel/HSV/RGB/HEX picker, or enter an exact #RRGGBB value.",
    "theme_sizing_control":"Adjust spacing, sizing or density live. Use the slider for quick tuning and the number field when you need an exact value.",
    "theme_font_control":"Choose an installed font. Type part of a font name to filter the dropdown, then select the family you want to preview live.",
    "theme_studio_close":"Close Theme Studio. Unsaved preview changes are discarded; use Save as New Theme first if you want to keep them.",
    "color_picker":"Choose a colour using the wheel, HSV, RGB or exact HEX values. The swatch shows the resulting colour before it is applied.",
    "color_eyedropper":"After two seconds, sample the pixel under the mouse pointer anywhere visible on the desktop. This requires Pillow and OS screen-capture support.",
})
DEFAULT_MESSAGES = {'a_preview_is_already_rendering_cancel_it_or_wait_c2c6d67e': 'A preview is already rendering. Cancel it or '
                                                              'wait before rendering again.',
 'archive_must_contain_exactly_one_footage_lab_app_c7a5e382': 'Archive must contain exactly one Footage Lab '
                                                              'application',
 'built_in_preset_names_cannot_be_overwritten_choo_177b69d9': 'Built-in preset names cannot be overwritten. '
                                                              'Choose another name.',
 'byte_identical_copy_cde81ae3': 'Byte-identical copy',
 'cancel_running_conversion_and_quit_2fec9be1': 'Cancel running conversion and quit?',
 'cancel_the_running_job_before_repairing_it_a0bc166e': 'Cancel the running job before repairing it.',
 'cancelled_d353a99e': 'Cancelled',
 'cannot_losslessly_split_v0_below_the_selected_si_e1c97571': 'Cannot losslessly split {v0} below the '
                                                              'selected size because there is no suitable '
                                                              'intermediate keyframe. Increase Max upload '
                                                              'MiB or use Glitch derivative/re-encode mode.',
 'checking_omne_space_for_updates_a507c77b': 'Checking omne.space for updates…',
 'copied_diagnostics_to_clipboard_44b3b48c': 'Copied diagnostics to clipboard',
 'could_not_launch_update_installer_v0_762cb5cd': 'Could not launch update installer:\n{v0}',
 'could_not_save_preferences_v0_bf273d4c': 'Could not save preferences:\n{v0}',
 'count_output_s_ready_f187af59': '{count} output(s) ready',
 'defaults_restored_0a4a35c2': 'Defaults restored',
 'defaults_restored_no_folder_scanned_fbda0958': 'Defaults restored · no folder scanned',
 'downloading_update_v0_0f_3799f0f9': 'Downloading update… {v0:.0f}%',
 'downloading_v_v0_83c9f891': 'Downloading v{v0}…',
 'duplicate_archive_paths_531a1605': 'Duplicate archive paths',
 'finish_or_cancel_the_preview_and_queued_conversi_e4d8e36f': 'Finish or cancel the preview and queued '
                                                              'conversions before installing an update.',
 'folder_not_found_v0_a1fe40b4': 'Folder not found:\n{v0}',
 'generation_v0_v1_2bc7f3da': 'Generation {v0}/{v1}',
 'glitch_v0_v1_v2_g_fps_crf_v3_v4_b4398fcb': 'GLITCH · {v0} · {v1} @ {v2:g} fps · CRF {v3}{v4}',
 'idle_ab0171ca': 'Idle',
 'incomplete_release_file_manifest_4acedd98': 'Incomplete release file manifest',
 'install_footage_lab_v_v0_from_omne_space_user_se_f856d243': 'Install Footage Lab v{v0} from omne.space?\n'
                                                              '\n'
                                                              'User settings and media are kept. The current '
                                                              'application will be backed up.',
 'invalid_public_file_manifest_45262dbe': 'Invalid public file manifest',
 'invalid_update_manifest_b84294b7': 'Invalid update manifest',
 'lossless_original_video_audio_streams_preserved__9335f979': 'LOSSLESS · original video/audio streams '
                                                              'preserved · split only when required · ≤ '
                                                              '{v0:g} MiB',
 'lossless_split_v0_s_24a6ba48': 'Lossless split · {v0}s',
 'malformed_checksum_file_7f5e41e4': 'Malformed checksum file',
 'missing_output_v0_fb7fda6f': 'Missing output {v0}',
 'missing_v0_linux_install_ffmpeg_with_your_packag_ac15edc3': 'Missing: {v0}\n'
                                                              '\n'
                                                              'Linux: install FFmpeg with your package '
                                                              'manager.\n'
                                                              'Windows: install FFmpeg or use the packaged '
                                                              'release that bundles it.',
 'no_encoded_clips_were_produced_use_copy_diagnost_97d18b13': 'No encoded clips were produced; use Copy '
                                                              'Diagnostics to inspect the FFmpeg log',
 'no_folder_scanned_15a35e30': 'No folder scanned',
 'oversize_output_v0_778836f1': 'Oversize output {v0}',
 'overwrite_custom_preset_v0_a23b5bc9': 'Overwrite custom preset "{v0}"?',
 'package_version_does_not_match_update_manifest_853514dd': 'Package version does not match update manifest',
 'preferences_saved_3490b974': 'Preferences saved',
 'preparing_preview_frames_73374815': 'Preparing preview frames',
 'preset_name_cannot_be_empty_3a0b594c': 'Preset name cannot be empty.',
 'preview_cancelled_c486a275': 'Preview cancelled',
 'preview_display_error_v0_ef4379ca': 'Preview display error: {v0}',
 'preview_failed_open_diagnostics_for_the_ffmpeg_e_a0218765': 'Preview failed · open Diagnostics for the '
                                                              'FFmpeg error',
 'preview_failed_use_diagnostics_to_copy_the_log_c4d62686': 'Preview failed\n'
                                                            'Use Diagnostics… to copy the log',
 'preview_is_paused_while_batch_conversions_are_qu_d3ae7f01': 'Preview is paused while batch conversions are '
                                                              'queued/running to preserve performance.',
 'preview_render_completed_but_no_display_frames_w_b9ddf2d6': 'Preview render completed but no display '
                                                              'frames were produced',
 'preview_tests_the_current_glitch_settings_using__23f5cb9c': 'Preview tests the current glitch settings '
                                                              'using a fast proxy.',
 'private_owner_file_is_not_permitted_in_a_public__d3279504': 'Private/owner file is not permitted in a '
                                                              'public application update',
 'proxy_resolution_fps_g_fps_0158653d': 'Proxy {resolution} @ {fps:g} fps',
 'release_file_checksum_mismatch_v0_3bcc5a3d': 'Release file checksum mismatch: {v0}',
 'rendering_preview_62c00342': 'Rendering preview…',
 'rendering_preview_a4fb3ebc': 'Rendering preview',
 'rendering_v0_74fcd733': 'Rendering {v0}',
 'repairing_oversize_clip_3b81cb5f': 'Repairing oversize clip',
 'required_runtime_files_are_absent_55d57aa9': 'Required runtime files are absent',
 'reset_folders_and_inspector_controls_to_applicat_529fff54': 'Reset folders and Inspector controls to '
                                                              'application defaults?\n'
                                                              '\n'
                                                              'Custom presets and job history will be kept.',
 'saved_custom_preset_v0_1220c1b7': 'Saved custom preset: {v0}',
 'starting_aeed4d26': 'Starting',
 'the_update_package_url_or_sha_256_checksum_is_in_5be63fc4': 'The update package URL or SHA-256 checksum is '
                                                              'invalid.',
 'the_verified_update_installer_has_been_launched__4a35074a': 'The verified update installer has been '
                                                              'launched. Close Footage Lab when the '
                                                              'installer asks you to.',
 'this_build_requires_a_compatible_installer_asset_2da5e2c2': 'This build requires a compatible installer '
                                                              'asset',
 'this_installer_is_not_for_the_current_platform_b2e21b9a': 'This installer is not for the current platform',
 'unreadable_video_v0_42368c0c': 'Unreadable video {v0}',
 'unsafe_installed_application_path_a5054a64': 'Unsafe installed application path',
 'unsafe_path_in_update_archive_82f7efcb': 'Unsafe path in update archive',
 'unsafe_release_file_path_23b2d1a1': 'Unsafe release file path',
 'untrusted_update_url_db55a77b': 'Untrusted update URL',
 'update_archive_exceeds_safety_limits_fa6f874b': 'Update archive exceeds safety limits',
 'update_check_unavailable_app_remains_fully_usabl_bd906e7e': 'Update check unavailable · app remains fully '
                                                              'usable',
 'update_checksum_mismatch_installation_was_not_at_3c090b0d': 'Update checksum mismatch; installation was '
                                                              'not attempted',
 'update_installation_failed_see_diagnostics_2d6081cd': 'Update installation failed · see Diagnostics',
 'update_installation_failed_v0_145a0097': 'Update installation failed:\n{v0}',
 'update_installed_successfully_restart_footage_la_c4762641': 'Update installed successfully. Restart '
                                                              'Footage Lab now?',
 'update_installer_downloaded_launching_eb146d1c': 'Update installer downloaded · launching…',
 'update_is_missing_release_files_json_237bb5d0': 'Update is missing release_files.json',
 'update_manifest_too_large_e4660666': 'Update manifest too large',
 'update_package_exceeds_download_limit_6cdbc18b': 'Update package exceeds download limit',
 'update_redirect_outside_the_permitted_https_host_132a2b85': 'Update redirect outside the permitted HTTPS '
                                                              'host',
 'update_v_v0_available_1d2cba5e': 'Update v{v0} available',
 'v0_failed_v1_log_v2_ed23ba34': '{v0} failed: {v1} | log: {v2}',
 'v0_ready_ec12e031': '{v0} · ready',
 'v0_rendering_643b01a8': '{v0} · rendering…',
 'v0_running_v1_queued_v2_done_v3_failed_28b2ee6e': '{v0} running · {v1} queued · {v2} done · {v3} failed',
 'v0_v1_24a4203e': '{v0} {v1}',
 'v0_v1_v2_2f_fps_v3_1f_s_v4_1f_mib_5f200bf8': '{v0}×{v1} · {v2:.2f} fps · {v3:.1f}s · {v4:.1f} MiB',
 'v0_videos_v1_2f_gib_3b56f743': '{v0} videos · {v1:.2f} GiB',
 'v_v0_available_no_v1_package_yet_6b87a044': 'v{v0} available · no {v1} package yet',
 'v_v0_installed_restart_required_3abfcfd3': 'v{v0} installed · restart required',
 'v_v0_up_to_date_85b8a61c': 'v{v0} · up to date',
 'v_v0_update_check_pending_65b9dd0d': 'v{v0} · update check pending'}
_ACTIVE_PROFILE = {}

def message_key(template):
    clean = re.sub(r"[^a-z0-9]+", "_", template.lower()).strip("_")[:48]
    return clean + "_" + hashlib.sha256(template.encode()).hexdigest()[:8]

def tr(template, **values):
    """Format an editable message; retain a working fallback on bad local edits."""
    result = _ACTIVE_PROFILE.get("messages", {}).get(message_key(template), template)
    try:
        return str(result).format(**values) if values else str(result)
    except (KeyError, ValueError, IndexError, AttributeError):
        return template.format(**values) if values else template

BUILTIN_THEMES = {
    "Pungent Purple": copy.deepcopy(DEFAULT_CHROME),
    "Midnight Syntax": {**copy.deepcopy(DEFAULT_CHROME),
        "background":"#0D1117","panel_bg":"#161B22","foreground":"#E6EDF3","muted_fg":"#8B949E",
        "field_bg":"#0D1117","field_fg":"#E6EDF3","button_bg":"#21262D","button_fg":"#E6EDF3",
        "active_bg":"#30363D","active_fg":"#FFFFFF","selection_bg":"#1F6FEB","accent":"#58A6FF","secondary_accent":"#D2A8FF",
        "tab_bg":"#161B22","tab_selected_bg":"#21262D","panel_edge":"#30363D","sash_color":"#484F58",
        "scrollbar_bg":"#484F58","scrollbar_trough":"#161B22","scale_bg":"#161B22","scale_trough":"#30363D",
        "preview_bg":"#010409","preview_fg":"#D2A8FF","success_fg":"#3FB950","warning_fg":"#D29922","failure_fg":"#F85149","running_fg":"#58A6FF",
        "tooltip_bg":"#21262D","tooltip_fg":"#E6EDF3"},
    "Lavender Haze": {**copy.deepcopy(DEFAULT_CHROME),
        "background":"#EDE7F6","panel_bg":"#F6F0FC","foreground":"#332B3D","muted_fg":"#74677F",
        "field_bg":"#FFFFFF","field_fg":"#332B3D","button_bg":"#DED0ED","button_fg":"#332B3D",
        "active_bg":"#CFB7E5","active_fg":"#241B2E","selection_bg":"#8E68B2","accent":"#7652A2","secondary_accent":"#B88DDB",
        "tab_bg":"#E3D7EF","tab_selected_bg":"#FFFFFF","panel_edge":"#C7B4D8","sash_color":"#9E83B7",
        "scrollbar_bg":"#BCA7CD","scrollbar_trough":"#E7DDF0","scale_bg":"#F6F0FC","scale_trough":"#D2C0DF",
        "preview_bg":"#241A2E","preview_fg":"#F0DFFF","success_fg":"#2D8A4A","warning_fg":"#C77919","failure_fg":"#C63D62","running_fg":"#7652A2",
        "tooltip_bg":"#332B3D","tooltip_fg":"#F7F0FF"},
    "CRT Moss": {**copy.deepcopy(DEFAULT_CHROME),
        "background":"#0D1510","panel_bg":"#142019","foreground":"#D8E8D8","muted_fg":"#879A88",
        "field_bg":"#0A110D","field_fg":"#D8E8D8","button_bg":"#1C2C21","button_fg":"#D8E8D8",
        "active_bg":"#29412F","active_fg":"#FFF3B0","selection_bg":"#3A6141","accent":"#E7D45A","secondary_accent":"#8BCF8F",
        "tab_bg":"#142019","tab_selected_bg":"#1F3125","panel_edge":"#35513B","sash_color":"#4B6A50",
        "scrollbar_bg":"#4B6A50","scrollbar_trough":"#142019","scale_bg":"#142019","scale_trough":"#314737",
        "preview_bg":"#050806","preview_fg":"#A8E6A3","success_fg":"#6BD66F","warning_fg":"#F2A54A","failure_fg":"#E95072","running_fg":"#A8E6A3",
        "tooltip_bg":"#1C2C21","tooltip_fg":"#E6F3E6"},
}

def profile_defaults():
    return {"schema": 3, "identity": copy.deepcopy(DEFAULT_IDENTITY),
            "chrome": copy.deepcopy(DEFAULT_CHROME), "labels": copy.deepcopy(DEFAULT_LABELS),
            "tooltips": copy.deepcopy(DEFAULT_TOOLTIPS), "messages": copy.deepcopy(DEFAULT_MESSAGES),
            "elements": {}, "themes": copy.deepcopy(BUILTIN_THEMES),
            "published_themes": list(BUILTIN_THEMES), "default_theme": "Pungent Purple"}

def fields_in(template):
    return {f for _, f, _, _ in string.Formatter().parse(template) if f is not None}

def validate_ui_profile(data):
    if not isinstance(data, dict):
        raise ValueError("UI profile must be a JSON object")
    base = profile_defaults()
    for section in ("identity", "chrome", "labels", "tooltips", "messages", "elements", "themes"):
        if section in data and not isinstance(data[section], dict):
            raise ValueError(f"Profile section {section} must be an object")
    result = _merge_ui_profile(base, data)
    for section in ("labels", "messages"):
        for key, default in base[section].items():
            value = result[section].get(key)
            if not isinstance(value, str) or fields_in(default) != fields_in(value):
                raise ValueError(f"Keep the same template fields in {section}.{key}: {sorted(fields_in(default))}")
    for key, value in result["tooltips"].items():
        if not isinstance(value, str):raise ValueError(f"Tooltip {key} must be text")
    for key, default in DEFAULT_CHROME.items():
        value = result["chrome"][key]
        if isinstance(default, int):
            low, high = (50, 5000) if key == "tooltip_delay_ms" else (1, 1000)
            if isinstance(value, bool) or not isinstance(value, int) or not low <= value <= high:
                raise ValueError(f"Chrome {key} must be an integer from {low} to {high}")
        elif not isinstance(value, str):raise ValueError(f"Chrome {key} must be text")
        elif default.startswith("#") and not re.fullmatch(r"#[0-9a-fA-F]{6}", value):
            raise ValueError(f"Chrome {key} requires a #RRGGBB colour")
    themes=result.get("themes",{})
    if not themes or not isinstance(themes,dict): raise ValueError("At least one theme is required")
    for theme_name,theme_chrome in themes.items():
        if not isinstance(theme_name,str) or not theme_name.strip(): raise ValueError("Theme names must be non-empty text")
        if not isinstance(theme_chrome,dict): raise ValueError(f"Theme {theme_name} must be an object")
        merged={**copy.deepcopy(DEFAULT_CHROME),**theme_chrome}
        for key,default in DEFAULT_CHROME.items():
            value=merged.get(key)
            if isinstance(default,int):
                low,high=(50,5000) if key=="tooltip_delay_ms" else (1,1000)
                if isinstance(value,bool) or not isinstance(value,int) or not low<=value<=high: raise ValueError(f"Theme {theme_name}: {key} must be an integer from {low} to {high}")
            elif not isinstance(value,str): raise ValueError(f"Theme {theme_name}: {key} must be text")
            elif default.startswith("#") and not re.fullmatch(r"#[0-9a-fA-F]{6}",value): raise ValueError(f"Theme {theme_name}: {key} requires a #RRGGBB colour")
        themes[theme_name]=merged
    published=result.get("published_themes",[])
    if not isinstance(published,list): raise ValueError("published_themes must be a list")
    published=[x for x in published if isinstance(x,str) and x in themes]
    if not published: raise ValueError("Publish at least one theme")
    result["published_themes"]=list(dict.fromkeys(published))
    if result.get("default_theme") not in result["published_themes"]: result["default_theme"]=result["published_themes"][0]
    for key in ("website_url", "support_url"):
        url = urllib.parse.urlparse(result["identity"][key])
        if url.scheme != "https" or not url.hostname or url.username or url.password:
            raise ValueError(f"Identity {key} must be a public HTTPS URL")
    if any(c in str(result["identity"]["app_name"]) for c in "\n\r"):raise ValueError("Application name must be a single line")
    if not str(result["identity"]["app_name"]).strip():raise ValueError("Application name must not be empty")
    allowed = {"background", "foreground", "font_family", "font_size", "font_weight", "borderwidth", "padding", "relief"}
    for key, opts in result["elements"].items():
        if not isinstance(opts, dict) or set(opts) - allowed:
            raise ValueError(f"Unsupported element override in {key}; allowed: {sorted(allowed)}")
    return result

class AutoScrollbar(ttk.Scrollbar):
    """Scrollbar that disappears when the entire range is visible."""
    def set(self, first, last):
        try:
            hidden=float(first)<=0.0 and float(last)>=1.0
        except Exception:
            hidden=False
        if hidden:
            self.grid_remove()
        else:
            self.grid()
        super().set(first,last)

class ScrollSection(ttk.Frame):
    """Vertical-only responsive viewport.

    Content is always constrained to the visible cell width, so horizontal
    scrollbars never appear. Long explanatory labels can wrap inside that
    width, while controls stay clipped to their own cell boundaries. The
    vertical bar appears only when content actually exceeds the viewport.
    """
    def __init__(self, parent, *, height=120, chrome=None):
        super().__init__(parent, height=height, width=200)
        self.chrome=chrome or DEFAULT_CHROME
        self.grid_propagate(False)
        self.rowconfigure(0, weight=1); self.columnconfigure(0, weight=1)
        self.canvas=tk.Canvas(self,borderwidth=0,highlightthickness=0,width=1,height=1,
                              background=self.chrome["background"])
        self.body=ttk.Frame(self.canvas)
        self.window=self.canvas.create_window(0,0,anchor="nw",window=self.body)
        self.vbar=AutoScrollbar(self,orient="vertical",command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=self.vbar.set,yscrollincrement=22)
        self.canvas.grid(row=0,column=0,sticky="nsew")
        self.vbar.grid(row=0,column=1,sticky="ns")
        self._pending=None
        self.body.bind("<Configure>",self.schedule,add="+")
        self.canvas.bind("<Configure>",self.schedule,add="+")
    def schedule(self,event=None):
        if self._pending is None:self._pending=self.after_idle(self.reflow)
    def reflow(self):
        self._pending=None
        if not self.winfo_exists():return
        cw=max(1,self.canvas.winfo_width()); ch=max(1,self.canvas.winfo_height())
        self.canvas.itemconfigure(self.window,width=cw)
        self.body.update_idletasks()
        height=max(ch,self.body.winfo_reqheight())
        self.canvas.configure(scrollregion=(0,0,cw,height))
        if height<=ch:self.canvas.yview_moveto(0)
    def destroy(self):
        if self._pending:
            try:self.after_cancel(self._pending)
            except tk.TclError:pass
        super().destroy()
    def content_height(self):
        return self.body.winfo_reqheight()+3
    def wheel(self,event):
        units=(-1 if getattr(event,"num",None)==4 else 1) if getattr(event,"num",None) in (4,5) else (-1 if event.delta>0 else 1)
        self.canvas.yview_scroll(units*2,"units")
        return "break"

def bind_wrap(widget,pad=16,minimum=120):
    """Keep prose inside its cell instead of requiring horizontal scrolling."""
    def resize(event):
        try:widget.configure(wraplength=max(minimum,event.width-pad))
        except tk.TclError:pass
    widget.bind("<Configure>",resize,add="+")
    return widget

def install_wheel_router(root):
    """Route wheel gestures to the surface underneath the pointer.

    Tk's platform defaults are inconsistent when nested canvases, text fields,
    scales and comboboxes are involved. Footage Lab deliberately makes wheel
    behaviour spatial instead of focus-driven:

    - wheel: scroll the vertically scrollable field/area under the pointer;
    - Shift+wheel: pan the field under the pointer when it has horizontal
      overflow, otherwise scroll that field vertically, then fall back to the
      enclosing vertical area;
    - scales/spinboxes/comboboxes never change values merely because the mouse
      wheel passed over them.

    This keeps editor panels predictable on Windows, macOS and X11/Wayland.
    """
    def units(event):
        num=getattr(event,"num",None)
        if num in (4,6):return -2
        if num in (5,7):return 2
        delta=int(getattr(event,"delta",0) or 0)
        if delta==0:return 0
        step=max(1,abs(delta)//120) if abs(delta)>=120 else 1
        return -step if delta>0 else step

    def shifted(event):
        return getattr(event,"num",None) in (6,7) or bool(int(getattr(event,"state",0) or 0)&0x0001)

    def view_range(widget,axis):
        try:
            view=getattr(widget,axis+"view")()
            if not isinstance(view,(tuple,list)) or len(view)<2:return None
            return float(view[0]),float(view[1])
        except Exception:return None

    def can_scroll(widget,axis):
        rng=view_range(widget,axis)
        return bool(rng and (rng[0]>0.0005 or rng[1]<0.9995))

    def scroll(widget,axis,amount):
        if not amount:return False
        try:
            getattr(widget,axis+"view_scroll")(int(amount),"units")
            return True
        except Exception:return False

    field_types=(tk.Entry,ttk.Entry,ttk.Spinbox,ttk.Combobox,tk.Spinbox,tk.Text,ttk.Treeview,tk.Listbox)
    vertical_native=(tk.Text,ttk.Treeview,tk.Listbox)
    value_controls=(tk.Scale,ttk.Scale,tk.Spinbox,ttk.Spinbox,ttk.Combobox)

    def ancestry(widget):
        seen=set()
        while widget is not None and id(widget) not in seen:
            seen.add(id(widget));yield widget
            widget=getattr(widget,"master",None)

    def nearest_area(widget):
        for w in ancestry(widget):
            if isinstance(w,ScrollSection) and can_scroll(w.canvas,"y"):
                return w.canvas
            if isinstance(w,tk.Canvas) and can_scroll(w,"y"):
                return w
        return None

    def route(event):
        amount=units(event)
        if not amount:return
        try:widget=root.winfo_containing(event.x_root,event.y_root)
        except tk.TclError:return
        if widget is None:return

        if shifted(event):
            for w in ancestry(widget):
                if isinstance(w,field_types):
                    if can_scroll(w,"x") and scroll(w,"x",amount*2):return "break"
                    if can_scroll(w,"y") and scroll(w,"y",amount*2):return "break"
                    break
            area=nearest_area(widget)
            if area is not None and scroll(area,"y",amount*2):return "break"
            return "break"

        for w in ancestry(widget):
            if isinstance(w,vertical_native):
                if can_scroll(w,"y") and scroll(w,"y",amount*2):return "break"
                break
            if isinstance(w,value_controls):
                break
            if isinstance(w,tk.Canvas) and can_scroll(w,"y"):
                if scroll(w,"y",amount*2):return "break"

        area=nearest_area(widget)
        if area is not None and scroll(area,"y",amount*2):return "break"
        return "break"

    tag="OmneScrollRoute"+str(id(root))
    for seq in ("<MouseWheel>","<Button-4>","<Button-5>","<Button-6>","<Button-7>","<Shift-MouseWheel>","<Shift-Button-4>","<Shift-Button-5>"):
        try:root.bind_class(tag,seq,route)
        except tk.TclError:pass

    def register(widget):
        try:
            tags=widget.bindtags()
            if tag not in tags:widget.bindtags((tag,)+tags)
            for child in widget.winfo_children():register(child)
        except tk.TclError:pass
    register(root)
    root._scroll_register=register

class FitPreview(tk.Frame):
    """Contains the entire frame for any aspect ratio; no internal scrolling."""
    def __init__(self,parent,chrome):
        self.chrome=chrome
        super().__init__(parent,bg=chrome["preview_bg"],highlightthickness=chrome["border_width"],
                         highlightbackground=chrome["panel_edge"],width=240,height=135)
        self.pack_propagate(False); self.grid_propagate(False)
        self.canvas=tk.Canvas(self,bg=chrome["preview_bg"],highlightthickness=0,width=1,height=1)
        self.canvas.pack(fill="both",expand=True)
        self.item=self.canvas.create_image(0,0,anchor="center")
        self.caption=self.canvas.create_text(0,0,fill=chrome["preview_fg"],
                          font=(chrome["font_family"],chrome["font_size"]),justify="center")
        self.raw=None; self.path=None; self.photo=None; self.after_resize=None
        self.cache=OrderedDict(); self.display_size=(0,0)
        self.canvas.bind("<Configure>",self.schedule,add="+")
    def set_chrome(self,chrome):
        self.chrome=chrome
        self.configure(bg=chrome["preview_bg"],highlightthickness=chrome["border_width"],highlightbackground=chrome["panel_edge"])
        self.canvas.configure(bg=chrome["preview_bg"])
        self.canvas.itemconfigure(self.caption,fill=chrome["preview_fg"],font=(chrome["font_family"],chrome["font_size"]))
        self.repaint()
    def configure(self,cnf=None,**kw):
        # Compat with the original App's placeholder calls.
        if "text" in kw:self.canvas.itemconfigure(self.caption,text=kw.pop("text"))
        if "image" in kw:
            value=kw.pop("image")
            if not value:
                self.raw=None; self.photo=None; self.path=None
                self.canvas.itemconfigure(self.item,image="")
        if cnf or kw:super().configure(cnf,**kw)
    config=configure
    def schedule(self,event=None):
        if self.after_resize:
            try:self.after_cancel(self.after_resize)
            except tk.TclError:pass
        self.after_resize=self.after(35,self.repaint)
    def show_frame(self,path):
        path=str(path)
        if path not in self.cache:
            if Image:
                with Image.open(path) as im:self.cache[path]=im.convert("RGB")
            else:self.cache[path]=tk.PhotoImage(master=self,file=path)
            # Small proxy cache, capped at four decoded frames.
            while len(self.cache)>4:self.cache.popitem(last=False)
        self.raw=self.cache[path]; self.cache.move_to_end(path); self.path=path
        self.canvas.itemconfigure(self.caption,text="")
        self.repaint()
    def repaint(self):
        self.after_resize=None
        if not self.winfo_exists():return
        w=max(1,self.canvas.winfo_width()-4); h=max(1,self.canvas.winfo_height()-4)
        cx=self.canvas.winfo_width()/2; cy=self.canvas.winfo_height()/2
        self.canvas.coords(self.item,cx,cy); self.canvas.coords(self.caption,cx,cy)
        # Only the empty/error caption may wrap; it is not a control label.
        self.canvas.itemconfigure(self.caption,width=max(1,w-8))
        if self.raw is None:return
        if Image and isinstance(self.raw,Image.Image):
            scaled=self.raw.copy()
            # thumbnail() is available across the older Pillow versions found in
            # distro repositories and preserves whole-frame aspect ratio.
            scaled.thumbnail((w,h),resample=_PIL_BILINEAR)
            self.photo=ImageTk.PhotoImage(scaled,master=self)
            self.display_size=scaled.size
        else:
            factor=max(1,math.ceil(max(self.raw.width()/w,self.raw.height()/h)))
            self.photo=self.raw.subsample(factor,factor)
            self.display_size=(self.photo.width(),self.photo.height())
        self.canvas.itemconfigure(self.item,image=self.photo)


    def destroy(self):
        if self.after_resize:
            try:self.after_cancel(self.after_resize)
            except tk.TclError:pass
        self.cache.clear()
        super().destroy()

def configure_theme(root, chrome):
    """Apply the semantic chrome palette to all ttk classes.

    Keep this centralized so changing a running theme updates every class rather
    than only widgets created after the switch.
    """
    style=ttk.Style(root)
    if "clam" in style.theme_names():style.theme_use("clam")
    font=(chrome["font_family"],chrome["font_size"])
    heading=(chrome["font_family"],chrome["heading_size"],"bold")
    root.option_add("*Font",font)
    style.configure(".",background=chrome["panel_bg"],foreground=chrome["foreground"],font=font,
                    borderwidth=chrome["border_width"],bordercolor=chrome["panel_edge"],
                    lightcolor=chrome["panel_edge"],darkcolor=chrome["panel_edge"],
                    troughcolor=chrome["scrollbar_trough"],focuscolor=chrome["accent"])
    style.configure("TFrame",background=chrome["panel_bg"])
    style.configure("TLabel",background=chrome["panel_bg"],foreground=chrome["foreground"])
    style.configure("Muted.TLabel",background=chrome["panel_bg"],foreground=chrome["muted_fg"])
    style.configure("Title.TLabel",background=chrome["panel_bg"],foreground=chrome["foreground"],font=heading)
    style.configure("Welcome.TLabel",background=chrome["panel_bg"],foreground=chrome["foreground"],font=(chrome["font_family"],chrome["welcome_size"],"bold"))
    style.configure("TLabelframe",background=chrome["panel_bg"],bordercolor=chrome["panel_edge"],lightcolor=chrome["panel_edge"],darkcolor=chrome["panel_edge"])
    style.configure("TLabelframe.Label",background=chrome["panel_bg"],foreground=chrome["foreground"],font=font)
    style.configure("TButton",background=chrome["button_bg"],foreground=chrome["button_fg"],padding=(chrome["button_pad_x"],chrome["button_pad_y"]),bordercolor=chrome["panel_edge"])
    style.configure("Collapse.TButton",background=chrome["panel_bg"],foreground=chrome["secondary_accent"],padding=(6,2),anchor="w",relief="flat",borderwidth=0)
    style.map("Collapse.TButton",background=[("active",chrome["active_bg"])],foreground=[("active",chrome["active_fg"])])
    style.map("TButton",background=[("pressed",chrome["selection_bg"]),("active",chrome["active_bg"])],foreground=[("disabled",chrome["disabled_fg"]),("active",chrome["active_fg"])])
    for st in ("TCheckbutton","TRadiobutton"):
        style.configure(st,background=chrome["panel_bg"],foreground=chrome["foreground"])
        style.map(st,background=[("active",chrome["panel_bg"])],foreground=[("disabled",chrome["disabled_fg"]),("active",chrome["active_fg"])])
    for st in ("TEntry","TCombobox","TSpinbox"):
        style.configure(st,fieldbackground=chrome["field_bg"],background=chrome["field_bg"],foreground=chrome["field_fg"],selectbackground=chrome["selection_bg"],selectforeground=chrome["selection_fg"],arrowcolor=chrome["secondary_accent"],bordercolor=chrome["panel_edge"],lightcolor=chrome["panel_edge"],darkcolor=chrome["panel_edge"])
        style.map(st,fieldbackground=[("readonly",chrome["field_bg"]),("disabled",chrome["panel_bg"])],foreground=[("disabled",chrome["disabled_fg"]),("readonly",chrome["field_fg"])],selectbackground=[("!disabled",chrome["selection_bg"])])
    style.configure("TNotebook",background=chrome["background"],bordercolor=chrome["panel_edge"],tabmargins=(2,2,2,0))
    style.configure("TNotebook.Tab",background=chrome["tab_bg"],foreground=chrome["foreground"],padding=(10,4),bordercolor=chrome["panel_edge"])
    style.map("TNotebook.Tab",background=[("selected",chrome["tab_selected_bg"]),("active",chrome["active_bg"])],foreground=[("selected",chrome["selection_fg"]),("active",chrome["active_fg"])])
    style.configure("Treeview",background=chrome["field_bg"],fieldbackground=chrome["field_bg"],foreground=chrome["field_fg"],rowheight=chrome["row_height"],bordercolor=chrome["panel_edge"])
    style.map("Treeview",background=[("selected",chrome["selection_bg"])],foreground=[("selected",chrome["selection_fg"])])
    style.configure("Treeview.Heading",background=chrome["button_bg"],foreground=chrome["button_fg"],bordercolor=chrome["panel_edge"])
    for st in ("Horizontal.TScrollbar","Vertical.TScrollbar"):
        style.configure(st,background=chrome["scrollbar_bg"],troughcolor=chrome["scrollbar_trough"],arrowcolor=chrome["foreground"],bordercolor=chrome["panel_edge"],arrowsize=chrome["scrollbar_width"])
        style.map(st,background=[("active",chrome["active_bg"])])
    style.configure("Horizontal.TProgressbar",background=chrome["accent"],troughcolor=chrome["scrollbar_trough"],bordercolor=chrome["panel_edge"])
    style.configure("TSeparator",background=chrome["panel_edge"])
    root.configure(background=chrome["background"])
    return style


def apply_element_style(widget,key,profile):
    """Optional fine-grained overrides, indexed by semantic key + Tk class."""
    cls=widget.winfo_class(); opts=profile.get("elements",{}).get(key+"."+cls,{})
    if not opts:return
    opts=copy.deepcopy(opts)
    family=opts.pop("font_family",profile["chrome"]["font_family"])
    size=opts.pop("font_size",profile["chrome"]["font_size"])
    weight=opts.pop("font_weight","normal")
    font=(family,size,weight)
    if isinstance(widget,ttk.Widget):
        name=re.sub(r"[^a-zA-Z0-9_]","_",key)+"."+cls
        ttk.Style(widget).configure(name,font=font,**opts); widget.configure(style=name)
    else:
        allowed=set(widget.keys()); opts={k:v for k,v in opts.items() if k in allowed}
        if "font" in allowed:opts["font"]=font
        if "padding" in opts:opts.pop("padding")
        widget.configure(**opts)


_THEME_COLOUR_KEYS=[k for k,v in profile_defaults()["chrome"].items() if isinstance(v,str) and re.fullmatch(r"#[0-9a-fA-F]{6}",v)]
_THEME_NUMBER_KEYS=[k for k,v in profile_defaults()["chrome"].items() if isinstance(v,int) and k not in {"tooltip_delay_ms"}]
_THEME_TEXT_KEYS=[k for k,v in profile_defaults()["chrome"].items() if isinstance(v,str) and k not in _THEME_COLOUR_KEYS]
_THEME_COLOUR_ORDER=[
    "background","panel_bg","field_bg","foreground","muted_fg","button_bg","button_fg","active_bg",
    "selection_bg","accent","secondary_accent","tab_bg","tab_selected_bg","panel_edge","sash_color","preview_bg",
    "success_fg","warning_fg","failure_fg","running_fg","tooltip_bg","tooltip_fg",
    "field_fg","active_fg","selection_fg","disabled_fg","scrollbar_bg","scrollbar_trough","scale_bg","scale_trough","preview_fg",
]
_THEME_COLOUR_ORDER=[k for k in _THEME_COLOUR_ORDER if k in _THEME_COLOUR_KEYS]+[k for k in _THEME_COLOUR_KEYS if k not in _THEME_COLOUR_ORDER]
_THEME_LABELS={
    "background":"Window","panel_bg":"Panels","panel_edge":"Panel edge","field_bg":"Fields","field_fg":"Field text",
    "foreground":"Text","muted_fg":"Muted text","button_bg":"Buttons","button_fg":"Button text","active_bg":"Hover / active",
    "active_fg":"Active text","accent":"Primary accent","secondary_accent":"Secondary accent","selection_bg":"Selection","selection_fg":"Selection text",
    "tab_bg":"Tabs","tab_selected_bg":"Selected tab","preview_bg":"Preview background","preview_fg":"Preview text","success_fg":"Success",
    "warning_fg":"Warning","failure_fg":"Error","running_fg":"Running","sash_color":"Resize edge","scrollbar_bg":"Scrollbar","scrollbar_trough":"Scrollbar trough",
    "scale_bg":"Slider background","scale_trough":"Slider trough","tooltip_bg":"Tooltip background","tooltip_fg":"Tooltip text",
}

for _key,_label in _THEME_LABELS.items():
    DEFAULT_LABELS.setdefault("theme_label."+_key,_label)


class UserThemeStudio(tk.Toplevel):
    """Compact live theme editor for public users.

    The visual structure mirrors the owner's Chrome Studio: paired semantic
    colours first, then sizing/density sliders and searchable fonts. Edits are
    previewed directly on the running app. Only an explicit Save creates a
    persistent personal theme; closing the studio restores the last saved
    appearance.
    """
    RANGES={
        "font_size":(7,18,1),"heading_size":(8,26,1),"welcome_size":(10,34,1),
        "panel_padding":(2,24,1),"button_pad_x":(2,20,1),"button_pad_y":(1,14,1),
        "border_width":(1,5,1),"row_height":(18,40,1),"sash_width":(3,14,1),
        "handle_size":(5,18,1),"handle_offset":(4,50,1),"scrollbar_width":(8,22,1),
        "slider_length":(100,320,5),"tooltip_font_size":(8,16,1),"tooltip_wrap_px":(220,700,10),
        "mono_size":(8,16,1),"tooltip_delay_ms":(100,1500,25),
    }
    def __init__(self,app):
        super().__init__(app);self.app=app;self.title(app.t("customize_theme","Customize Theme"));self.transient(app)
        self.geometry("780x690");self.minsize(680,580);self.protocol("WM_DELETE_WINDOW",self.close);self.bind("<Escape>",lambda _e:self.close())
        self.base_name=app.theme_name.get() if app.theme_name.get() in app.theme_library else app.default_theme
        self.session_original_name=self.base_name;self.session_original_chrome=copy.deepcopy(app.ui_chrome)
        self.original_name=self.base_name;self.original_chrome=copy.deepcopy(app.ui_chrome);self.vars={};self._loading=False;self._saved=False
        outer=ttk.Frame(self,padding=10);outer.pack(fill="both",expand=True)
        top=ttk.Frame(outer);top.pack(fill="x",pady=(0,7));top.columnconfigure(1,weight=1)
        theme_label=app.add_tip(ttk.Label(top,text=app.t("theme_studio_theme","Theme")),"theme_studio_theme");theme_label.grid(row=0,column=0,sticky="w")
        self.base=tk.StringVar(value=self.base_name)
        self.combo=app.add_tip(ttk.Combobox(top,textvariable=self.base,values=app.available_themes,state="readonly"),"theme_studio_theme");self.combo.grid(row=0,column=1,sticky="ew",padx=6);self.combo.bind("<<ComboboxSelected>>",lambda e:self.load_base())
        save_btn=app.add_tip(ttk.Button(top,text=app.t("theme_studio_save","Save as New Theme…"),command=self.save_as),"theme_studio_save");save_btn.grid(row=0,column=2,padx=(0,4))
        rev_btn=app.add_tip(ttk.Button(top,text=app.t("theme_studio_revert","Revert"),command=self.revert),"theme_studio_revert");rev_btn.grid(row=0,column=3)

        holder=ttk.Frame(outer);holder.pack(fill="both",expand=True);holder.rowconfigure(0,weight=1);holder.columnconfigure(0,weight=1)
        self.canvas=tk.Canvas(holder,highlightthickness=0,background=app.ui_chrome["background"]);self.canvas.grid(row=0,column=0,sticky="nsew")
        self.vbar=AutoScrollbar(holder,orient="vertical",command=self.canvas.yview);self.vbar.grid(row=0,column=1,sticky="ns");self.canvas.configure(yscrollcommand=self.vbar.set,yscrollincrement=22)
        self.body=ttk.Frame(self.canvas,padding=(4,2,8,8));self.win=self.canvas.create_window(0,0,window=self.body,anchor="nw")
        self.body.bind("<Configure>",lambda e:self.canvas.configure(scrollregion=self.canvas.bbox("all")));self.canvas.bind("<Configure>",lambda e:self.canvas.itemconfigure(self.win,width=e.width))

        ttk.Label(self.body,text=app.t("theme_studio_palette","Palette"),style="Title.TLabel").pack(anchor="w",pady=(0,5))
        palette=ttk.Frame(self.body);palette.pack(fill="x")
        for i,key in enumerate(_THEME_COLOUR_ORDER):
            row=i//2;group=i%2;col=group*3
            label=app.t("theme_label."+key,_THEME_LABELS.get(key,key.replace("_"," ").title()))
            lab=app.add_tip(ttk.Label(palette,text=label),"theme_palette_control");lab.grid(row=row,column=col,sticky="w",padx=(0,4),pady=3)
            var=tk.StringVar();self.vars[key]=var
            sw=app.add_tip(tk.Button(palette,width=3,relief="solid",bd=1,command=lambda k=key:self.pick(k)),"theme_palette_control");sw.grid(row=row,column=col+1,padx=2);var._swatch=sw
            ent=app.add_tip(ttk.Entry(palette,textvariable=var,width=10),"theme_palette_control");ent.grid(row=row,column=col+2,sticky="ew",padx=(0,12));var.trace_add("write",lambda *_a,k=key:self.changed(k))
        palette.columnconfigure(2,weight=1);palette.columnconfigure(5,weight=1)

        ttk.Separator(self.body).pack(fill="x",pady=10)
        ttk.Label(self.body,text=app.t("theme_studio_sizing","Sizing & density"),style="Title.TLabel").pack(anchor="w",pady=(0,5))
        for key in _THEME_NUMBER_KEYS+["tooltip_delay_ms"]:
            if key not in self.RANGES:continue
            lo,hi,step=self.RANGES[key];row=ttk.Frame(self.body);row.pack(fill="x",pady=2);row.columnconfigure(1,weight=1)
            lab=app.add_tip(ttk.Label(row,text=app.t("theme_label."+key,key.replace("_"," ").title()),width=22),"theme_sizing_control");lab.grid(row=0,column=0,sticky="w")
            var=tk.IntVar();self.vars[key]=var
            sc=app.add_tip(tk.Scale(row,from_=lo,to=hi,resolution=step,orient="horizontal",showvalue=False,variable=var,highlightthickness=0,command=lambda _v,k=key:self.changed(k)),"theme_sizing_control");sc.grid(row=0,column=1,sticky="ew",padx=(0,5))
            sp=app.add_tip(ttk.Spinbox(row,from_=lo,to=hi,increment=step,textvariable=var,width=7,command=lambda k=key:self.changed(k)),"theme_sizing_control");sp.grid(row=0,column=2);var.trace_add("write",lambda *_a,k=key:self.changed(k))

        ttk.Separator(self.body).pack(fill="x",pady=10)
        for key,label in [("font_family","Font family"),("mono_font","Monospace font")]:
            row=ttk.Frame(self.body);row.pack(fill="x",pady=2);row.columnconfigure(1,weight=1)
            lab=app.add_tip(ttk.Label(row,text=app.t("theme_label."+key,label),width=22),"theme_font_control");lab.grid(row=0,column=0,sticky="w")
            var=tk.StringVar();self.vars[key]=var
            combo=app.add_tip(SearchableFontCombobox(row,textvariable=var),"theme_font_control");combo.grid(row=0,column=1,sticky="ew");combo.bind("<<ComboboxSelected>>",lambda _e,k=key:self.changed(k));var.trace_add("write",lambda *_a,k=key:self.changed(k))

        note=ttk.Label(self.body,text=app.t("theme_studio_note","Changes update the running interface immediately. Saved themes stay on this computer and do not change the owner's approved public theme library."),style="Muted.TLabel",justify="left")
        note.pack(fill="x",pady=(10,0));bind_wrap(note,pad=12,minimum=220)
        foot=ttk.Frame(outer);foot.pack(fill="x",pady=(8,0));close_btn=app.add_tip(ttk.Button(foot,text=app.t("close","Close"),command=self.close),"theme_studio_close");close_btn.pack(side="right")
        self.load_base()
        if hasattr(app,"_scroll_register"):app._scroll_register(self)
        self.grab_set()

    def current(self):
        result=copy.deepcopy(self.original_chrome)
        for key,var in self.vars.items():
            try:
                if isinstance(var,tk.IntVar):result[key]=int(var.get())
                else:result[key]=str(var.get())
            except Exception:pass
        return {**copy.deepcopy(DEFAULT_CHROME),**result}

    def load_base(self):
        name=self.base.get();chrome=self.app.theme_library.get(name,self.app.ui_chrome);self._loading=True;self.original_chrome=copy.deepcopy(chrome)
        for key,var in self.vars.items():
            try:var.set(chrome.get(key,DEFAULT_CHROME.get(key,"")))
            except Exception:pass
        self._loading=False;self._saved=False;self.app.apply_theme(name,save=False,chrome_override=self.current());self.repaint_swatches()

    def repaint_swatches(self):
        for key in _THEME_COLOUR_ORDER:
            var=self.vars.get(key)
            if var:
                try:var._swatch.configure(bg=var.get(),activebackground=var.get())
                except Exception:pass
        try:self.canvas.configure(background=self.current()["background"])
        except Exception:pass

    def changed(self,key):
        if self._loading:return
        if key in _THEME_COLOUR_KEYS and not re.fullmatch(r"#[0-9a-fA-F]{6}",str(self.vars[key].get())):return
        self._saved=False;self.repaint_swatches();self.app.apply_theme(self.base.get(),save=False,chrome_override=self.current())

    def pick(self,key):
        value=AdvancedColorPicker.choose(self,self.vars[key].get(),self.app.t("theme_pick_title","Choose ")+self.app.t("theme_label."+key,_THEME_LABELS.get(key,key)))
        if value:self.vars[key].set(value.upper())

    def save_as(self):
        name=simpledialog.askstring(APP,self.app.t("theme_name_prompt","Theme name:"),parent=self)
        if not name or not name.strip():return
        name=name.strip()
        if name in self.app.published_themes and name not in self.app.user_themes:
            if not messagebox.askyesno(APP,self.app.t("theme_override_builtin","That is an approved built-in theme. Save a local theme with the same name and override it only on this computer?"),parent=self):return
        elif name in self.app.user_themes:
            if not messagebox.askyesno(APP,self.app.t("theme_override_local","A personal theme with this name already exists. Replace it?"),parent=self):return
        chrome=self.current();self.app.user_themes[name]=copy.deepcopy(chrome);save_user_themes(self.app.user_themes);self.app.theme_library[name]=copy.deepcopy(chrome);self.app.refresh_theme_choices();self.app.theme_name.set(name);self.app.apply_theme(name,save=True);self.base.set(name);self.original_name=name;self.original_chrome=copy.deepcopy(chrome);self.session_original_name=name;self.session_original_chrome=copy.deepcopy(chrome);self._saved=True
        messagebox.showinfo(APP,self.app.t("theme_saved","Saved local theme: {name}").format(name=name),parent=self)

    def revert(self):self.load_base()
    def close(self):
        # Theme Studio is a live preview surface. If the user did not explicitly
        # save a personal theme, return to the appearance that was active when
        # the editor opened. This prevents accidental preference changes from a
        # half-finished slider drag.
        if not self._saved:
            try:self.app.apply_theme(self.session_original_name,save=False,chrome_override=self.session_original_chrome)
            except Exception:pass
        try:self.grab_release()
        except tk.TclError:pass
        self.destroy()

@dataclass
class Job:
    id:str
    source:str
    mode:str
    preset:str
    settings:dict
    status:str="queued"
    progress:float=0
    message:str=""
    outputs:list[str]=field(default_factory=list)
    logs:list[str]=field(default_factory=list)

class Cancelled(Exception): pass

class SessionLog:
    def __init__(self):
        self.state_dir=user_state_dir()
        self.log_dir=self.state_dir/"logs"
        self.log_dir.mkdir(parents=True,exist_ok=True)
        stamp=time.strftime("%Y%m%d_%H%M%S")
        self.session=self.log_dir/f"session_{stamp}.log"
        self.lock=threading.Lock()
        self.counter=0
        self.write(f"{APP} {VERSION} session started")

    def write(self,message):
        line=f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] {message}"
        with self.lock:
            with self.session.open("a",encoding="utf-8") as h:
                h.write(line+"\n")

    def ffmpeg_log(self,task,stage):
        with self.lock:
            self.counter+=1
            n=self.counter
        name=f"{time.strftime('%Y%m%d_%H%M%S')}_{safe(str(task))}_{safe(stage)}_{n:04d}.log"
        return self.log_dir/name

    def tail(self,path=None,lines=80):
        target=Path(path) if path else self.session
        try:
            data=target.read_text(encoding="utf-8",errors="replace").splitlines()
            return "\n".join(data[-lines:])
        except Exception as e:
            return f"Unable to read {target}: {e}"

class Processor:
    def __init__(self, emit, logger, channel="batch"):
        self.emit=emit
        self.logger=logger
        self.channel=channel
        self.proc=None
        self.lock=threading.Lock()
        self.task_id=channel
        self.active_log=None

    def probe(self,p):
        cmd=[FFPROBE_BIN or "ffprobe","-v","error","-show_entries",
             "format=size,duration,bit_rate:stream=codec_type,codec_name,width,height,avg_frame_rate,bit_rate",
             "-of","json",str(p)]
        r=subprocess.run(cmd,capture_output=True,text=True)
        if r.returncode:
            self.logger.write(f"ffprobe failed for {p}: {r.stderr.strip()}")
            raise RuntimeError(r.stderr.strip() or f"ffprobe failed: {p}")
        d=json.loads(r.stdout or "{}"); f=d.get("format",{})
        v=next((x for x in d.get("streams",[]) if x.get("codec_type")=="video"),{})
        a=next((x for x in d.get("streams",[]) if x.get("codec_type")=="audio"),{})
        return dict(
            size=int(float(f.get("size") or p.stat().st_size)),
            dur=float(f.get("duration") or 0),
            vc=v.get("codec_name",""), ac=a.get("codec_name",""),
            w=int(v.get("width") or 0), h=int(v.get("height") or 0),
            fps=rate(v.get("avg_frame_rate","")),
            br=int(float(v.get("bit_rate") or f.get("bit_rate") or 0))
        )

    def set_task(self,task):
        self.task_id=str(task)

    def ffmpeg(self,args,dur,cb,cancel,stage="ffmpeg"):
        if cancel.is_set():raise Cancelled()
        cmd=[FFMPEG_BIN or "ffmpeg","-nostdin","-hide_banner","-loglevel","warning",
             "-progress","pipe:1","-nostats","-y"]+args
        log_path=self.logger.ffmpeg_log(self.task_id,stage)
        self.active_log=log_path
        self.logger.write(f"FFmpeg [{self.task_id}] {stage}: "+" ".join(map(str,cmd)))
        if self.channel=="preview":
            self.emit(preview_log=str(log_path))
        else:
            self.emit(job_id=self.task_id,log_file=str(log_path))
        last_progress=0.0
        with log_path.open("w",encoding="utf-8",errors="replace") as err:
            with self.lock:
                self.proc=subprocess.Popen(cmd,stdin=subprocess.DEVNULL,stdout=subprocess.PIPE,stderr=err,text=True,bufsize=1)
                p=self.proc
            try:
                assert p.stdout is not None
                for raw in p.stdout:
                    if cancel.is_set():
                        p.terminate()
                        try:p.wait(2)
                        except: p.kill()
                        self.logger.write(f"FFmpeg [{self.task_id}] {stage} cancelled")
                        raise Cancelled()
                    line=raw.strip()
                    if line.startswith(("out_time_us=","out_time_ms=")):
                        try:
                            sec=int(line.split("=",1)[1])/1e6
                            q=min(.995,sec/max(dur,.01))
                            if q-last_progress>=.002:
                                last_progress=q; cb(q)
                        except: pass
                    elif line=="progress=end": cb(1)
                rc=p.wait()
            finally:
                with self.lock:self.proc=None
        if rc:
            tail=self.logger.tail(log_path,18)
            self.logger.write(f"FFmpeg [{self.task_id}] {stage} FAILED rc={rc}\n{tail}")
            short=next((x for x in reversed(tail.splitlines()) if x.strip()),f"exit {rc}")
            raise RuntimeError(tr('{v0} failed: {v1} | log: {v2}', v0=stage, v1=short, v2=log_path))
        self.logger.write(f"FFmpeg [{self.task_id}] {stage} complete")

    def cancel(self):
        with self.lock:p=self.proc
        if p and p.poll() is None:
            try:
                p.terminate()
                try:p.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    p.kill(); p.wait(timeout=2)
            except Exception:pass

    def verify(self,p,maxb=None):
        if not p.exists() or not p.stat().st_size: raise RuntimeError(tr('Missing output {v0}', v0=p))
        inf=self.probe(p)
        if not inf["vc"]: raise RuntimeError(tr('Unreadable video {v0}', v0=p))
        if maxb and p.stat().st_size>maxb: raise RuntimeError(tr('Oversize output {v0}', v0=p.name))

    def dims(self,info,res):
        if res=="Source": return info["w"]//2*2, info["h"]//2*2
        w,h=res.split("x"); return int(w),int(h)

    def graph(self,info,s):
        w,h=self.dims(info,s["resolution"]); fps=float(s["fps"])
        chain=[f"scale={w}:{h}:flags=bicubic"]
        if s["interp"]:
            chain += [f"fps={float(s['interp_fps']):.3f}",
                      f"minterpolate=fps={fps:.3f}:mi_mode=mci:mc_mode=aobmc:me_mode=bidir:vsbmc=1"]
        else: chain += [f"fps={fps:.3f}"]
        parts=[f"[0:v]{','.join(chain)}[b]"]; cur="b"
        if s["warp"]>0:
            a=float(s["warp"]); sp=.03; mapdur=max(.1,float(info.get("dur",0) or .1))
            parts += [
                f"nullsrc=s={w}x{h}:r={fps:.3f}:d={mapdur:.3f},geq=lum='128+{a:.3f}*sin(Y/34+N*{sp:.4f})+{a*.3:.3f}*sin(X/80-N*{sp*.5:.4f})':cb=128:cr=128[x]",
                f"nullsrc=s={w}x{h}:r={fps:.3f}:d={mapdur:.3f},geq=lum='128+{a*.7:.3f}*sin(X/52-N*{sp*.8:.4f})':cb=128:cr=128[y]",
                f"[{cur}][x][y]displace=edge=mirror[w]"
            ]; cur="w"
        fs=[]
        if s["glow"]>0: fs.append(f"lagfun=decay={float(s['glow']):.4f}")
        if int(s["echo"])>1:
            n=int(s["echo"]); d=float(s["decay"])
            ws=" ".join(f"{max(.01,d**i):.4f}" for i in range(n))
            fs.append(f"tmix=frames={n}:weights='{ws}'")
        if s["chroma"]>0:
            c=int(round(float(s["chroma"])))
            fs.append(f"chromashift=cbh={-c}:crh={c}:cbv={max(0,c//3)}:crv={-max(0,c//3)}:edge=smear")
        if s["hue"]>0: fs.append(f"hue=h='{float(s['hue']):.3f}*sin(2*PI*t/8)':s=1")
        if abs(float(s["sat"])-1)>1e-3: fs.append(f"eq=saturation={float(s['sat']):.3f}")
        if s["blur"]>0: fs.append(f"gblur=sigma={float(s['blur']):.3f}")
        if s["scan"]>0:
            x=float(s["scan"])
            fs.append(f"geq=lum='lum(X,Y)*(1-{x:.4f}*(1-mod(Y,2)))':cb='cb(X,Y)':cr='cr(X,Y)'")
        parts.append(f"[{cur}]{','.join(fs) if fs else 'null'}[out]")
        return ";".join(parts)

    def gen_stage(self,src,info,s,work,job,cancel,start=None,length=None):
        cur=src; passes=int(s["generation"])
        w,h=self.dims(info,s["resolution"])
        for i in range(passes):
            out=work/f"gen{i+1}.avi"; args=[]
            if i==0 and start is not None: args += ["-ss",f"{start:.3f}"]
            args += ["-i",str(cur)]
            if i==0 and length is not None: args += ["-t",f"{length:.3f}"]
            args += ["-an","-vf",f"fps=15,scale={w}:{h}:flags=bicubic",
                     "-c:v","mpeg4","-q:v",str(10+i*5),"-g",str(120+i*60),
                     "-bf","0" if i==passes-1 else "2",str(out)]
            d=length if length else info["dur"]
            self.ffmpeg(args,d,lambda q,i=i:self.emit(job_id=job.id,progress=(i+q)/(passes+1)*.6,message=tr('Generation {v0}/{v1}', v0=i + 1, v1=passes)),cancel,stage=f"generation_{i+1}")
            cur=out
        return cur, self.probe(cur) if passes else info, passes>0 and (start is not None or length is not None)

    def split_oversize(self,p,maxb,work,cancel,job):
        q=[p]; final=[]
        while q:
            f=q.pop(0)
            if f.stat().st_size<=maxb: final.append(f); continue
            inf=self.probe(f); sub=Path(tempfile.mkdtemp(dir=work,prefix="resplit."))
            pat=sub/(f.stem+"__s%02d.mp4")
            self.ffmpeg(["-i",str(f),"-map","0","-c","copy","-f","segment",
                         "-segment_time",f"{max(.001,inf['dur']/2):.3f}","-reset_timestamps","1",
                         "-segment_format","mp4","-segment_format_options","movflags=+faststart",str(pat)],
                        inf["dur"],lambda x:self.emit(job_id=job.id,progress=.96+x*.03,message=tr('Repairing oversize clip')),cancel,stage="resplit_oversize")
            pieces=sorted(sub.glob("*.mp4"))
            if len(pieces)<2:
                raise RuntimeError(
                    tr('Cannot losslessly split {v0} below the selected size because there is no suitable intermediate keyframe. Increase Max upload MiB or use Glitch derivative/re-encode mode.', v0=f.name)
                )
            f.unlink(missing_ok=True); q=pieces+q
        return final

    def lossless(self,job,cancel):
        self.set_task(job.id)
        src=Path(job.source); s=job.settings; info=self.probe(src)
        root=Path(s["output"]).expanduser(); out=root/"MINIMAL_LOSSLESS"; work=root/"_WORK"
        out.mkdir(parents=True,exist_ok=True); work.mkdir(parents=True,exist_ok=True)
        maxb=int(float(s["max_mib"])*1048576); prefix=f"{safe(src.stem)}_{sid(src)}"
        existing=sorted(out.glob(prefix+"*"))
        if existing:
            try:
                for p in existing:self.verify(p,maxb)
                self.logger.write(f"[{job.id}] reusing {len(existing)} verified lossless outputs")
                return existing
            except Exception:
                for p in existing:p.unlink(missing_ok=True)
        wd=Path(tempfile.mkdtemp(dir=work,prefix=prefix+"."))
        try:
            if info["size"]<=maxb:
                t=wd/(prefix+".MP4"); shutil.copy2(src,t); files=[t]
                self.emit(job_id=job.id,progress=.9,message=tr('Byte-identical copy'))
            else:
                bps=info["size"]*8/max(info["dur"],.01)
                secs=max(3,min(120,int(maxb*8*.8/bps)))
                pat=wd/(prefix+"__p%03d.mp4")
                self.ffmpeg(["-i",str(src),"-map","0","-map_metadata","0","-c","copy",
                             "-f","segment","-segment_time",str(secs),"-reset_timestamps","1",
                             "-segment_format","mp4","-segment_format_options","movflags=+faststart",str(pat)],
                            info["dur"],lambda x:self.emit(job_id=job.id,progress=x*.9,message=tr('Lossless split · {v0}s', v0=secs)),cancel,stage="lossless_split")
                files=sorted(wd.glob(prefix+"__p*.mp4"))
            final=[]
            for f in list(files): final.extend(self.split_oversize(f,maxb,wd,cancel,job))
            published=[]
            for i,f in enumerate(final):
                name=f"{prefix}__p{i:03d}.mp4" if len(final)>1 else f"{prefix}.mp4"
                dest=out/name; shutil.move(str(f),dest); self.verify(dest,maxb); published.append(dest)
            return published
        finally: shutil.rmtree(wd,ignore_errors=True)

    def glitch(self,job,cancel,preview=False,start=0,length=6,preview_root=None):
        self.set_task(job.id)
        src=Path(job.source); s=copy.deepcopy(job.settings); info=self.probe(src)
        root=Path(preview_root) if preview else Path(s["output"]).expanduser()
        work=root/"_WORK"; work.mkdir(parents=True,exist_ok=True)
        folder=safe(job.preset.upper().replace(" ","_")) if job.preset!="Manual" else "MANUAL_"+hashlib.sha256(json.dumps(s,sort_keys=True).encode()).hexdigest()[:8]
        out=root/folder
        if preview:out.mkdir(parents=True,exist_ok=True)
        prefix=f"{safe(src.stem)}_{sid(src)}"
        wd=Path(tempfile.mkdtemp(dir=work,prefix=prefix+"."))
        try:
            cur,ci,sliced=self.gen_stage(src,info,s,wd,job,cancel,start if preview else None,length if preview else None)
            graph=self.graph(ci,s)
            if preview:
                target=out/"preview.mp4"; args=[]
                if not sliced: args += ["-ss",f"{start:.3f}"]
                args += ["-i",str(cur)]
                if not sliced: args += ["-t",f"{length:.3f}"]
                args += ["-filter_complex",graph,"-map","[out]","-an","-c:v","libx264","-preset","ultrafast","-crf","18","-pix_fmt","yuv420p","-movflags","+faststart",str(target)]
                self.ffmpeg(args,length,lambda x:self.emit(preview_progress=x*.8,preview_message=tr('Rendering preview')),cancel,stage="preview_render")
                frames=out/"frames"; frames.mkdir(exist_ok=True)
                self.ffmpeg(["-i",str(target),"-vf","fps=8,scale=480:-2:flags=bicubic","-frames:v",str(max(1,int(length*8))),str(frames/"f_%04d.png")],
                            length,lambda x:self.emit(preview_progress=.8+x*.2,preview_message=tr('Preparing preview frames')),cancel,stage="preview_frames")
                return target,frames
            maxb=int(float(s["max_mib"])*1048576); mbps=float(s["bitrate"])
            seg=max(4,min(180,int(maxb*8*.74/(mbps*1e6))))
            pat=wd/(prefix+"__p%03d.mp4")
            self.ffmpeg(["-i",str(cur),"-filter_complex",graph,"-map","[out]","-an",
                         "-c:v","libx264","-preset",s["x264"],"-crf",str(s["crf"]),
                         "-pix_fmt","yuv420p","-maxrate",f"{mbps:.2f}M","-bufsize",f"{mbps*2:.2f}M",
                         "-f","segment","-segment_time",str(seg),"-reset_timestamps","1",
                         "-segment_format","mp4","-segment_format_options","movflags=+faststart",str(pat)],
                        ci["dur"],lambda x:self.emit(job_id=job.id,progress=.6+x*.35,message=tr('Rendering {v0}', v0=job.preset)),cancel,stage="glitch_render")
            files=sorted(wd.glob(prefix+"__p*.mp4"))
            if not files:raise RuntimeError(tr('No encoded clips were produced; use Copy Diagnostics to inspect the FFmpeg log'))
            final=[]
            for f in files: final.extend(self.split_oversize(f,maxb,wd,cancel,job))
            out.mkdir(parents=True,exist_ok=True)
            published=[]
            for i,f in enumerate(final):
                dest=out/(f"{prefix}__p{i:03d}.mp4" if len(final)>1 else f"{prefix}.mp4")
                shutil.move(str(f),dest); self.verify(dest,maxb); published.append(dest)
            return published
        finally:
            if not preview: shutil.rmtree(wd,ignore_errors=True)

def trusted_download_url(url):
    u=urllib.parse.urlparse(str(url)); host=(u.hostname or "").lower()
    return u.scheme=="https" and not u.username and not u.password and u.port in (None,443) and (host=="omne.space" or host.endswith(".omne.space"))

class TrustedRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        if not trusted_download_url(newurl):raise RuntimeError(tr('Update redirect outside the permitted HTTPS host'))
        return super().redirect_request(req,fp,code,msg,headers,newurl)

def trusted_open(url,timeout=15):
    if not trusted_download_url(url):raise RuntimeError(tr('Untrusted update URL'))
    request=urllib.request.Request(url,headers={"User-Agent":f"Mozilla/5.0 (X11; Linux x86_64) OmN-e-Footage-Lab/{VERSION}","Cache-Control":"no-cache","Pragma":"no-cache","Accept":"application/json, application/octet-stream;q=0.9, */*;q=0.8"})
    return urllib.request.build_opener(TrustedRedirect()).open(request,timeout=timeout)

def install_source_package(archive, destination, backup_root, expected_version):
    """Validate completely, then replace public release files; rollback on failure.

    This function never executes a downloaded install script, accesses raw media,
    or writes into user preferences. Public packages contain no owner tool.
    """
    destination=Path(destination).resolve(); backup_root=Path(backup_root)
    backup_root.mkdir(parents=True,exist_ok=True)
    work=Path(tempfile.mkdtemp(prefix="checked-source.",dir=backup_root))
    try:
        with zipfile.ZipFile(archive) as z:
            items=z.infolist()
            if len(items)>300 or sum(i.file_size for i in items)>100*1024*1024:raise RuntimeError(tr('Update archive exceeds safety limits'))
            paths=[]
            for item in items:
                rel=Path(item.filename)
                if rel.is_absolute() or ".." in rel.parts or "\\" in item.filename or ":" in item.filename or (item.external_attr>>16)&0o170000==0o120000:
                    raise RuntimeError(tr('Unsafe path in update archive'))
                paths.append(item.filename)
            if len(paths)!=len(set(paths)):raise RuntimeError(tr('Duplicate archive paths'))
            z.extractall(work)
        scripts=list(work.rglob("omne_footage_lab.py"))
        if len(scripts)!=1:raise RuntimeError(tr('Archive must contain exactly one Footage Lab application'))
        release=scripts[0].parent
        manifest_path=release/"release_files.json"
        if not manifest_path.exists():raise RuntimeError(tr('Update is missing release_files.json'))
        meta=json.loads(manifest_path.read_text(encoding="utf-8"))
        names=meta.get("files",[])
        if not isinstance(names,list) or not names or len(names)!=len(set(names)):raise RuntimeError(tr('Invalid public file manifest'))
        required={"omne_footage_lab.py","ui_profile.json","release_files.json"}
        if not required.issubset(names):raise RuntimeError(tr('Required runtime files are absent'))
        sums={}
        for line in (release/"SHA256SUMS").read_text(encoding="utf-8").splitlines():
            digest,sep,name=line.partition("  ")
            if not sep or not re.fullmatch(r"[a-f0-9]{64}",digest):raise RuntimeError(tr('Malformed checksum file'))
            sums[name]=digest
        for name in names:
            rel=Path(name)
            if rel.is_absolute() or ".." in rel.parts or "\\" in name or ":" in name or any(x.startswith(".") for x in rel.parts):raise RuntimeError(tr('Unsafe release file path'))
            if any(word in name.lower() for word in ("customizer","customiser","publisher","preferences.json","custom_presets.json","credential","token","secret")):
                raise RuntimeError(tr('Private/owner file is not permitted in a public application update'))
            file=release/rel
            if not file.is_file() or name not in sums:raise RuntimeError(tr('Incomplete release file manifest'))
            if hashlib.sha256(file.read_bytes()).hexdigest()!=sums[name]:raise RuntimeError(tr('Release file checksum mismatch: {v0}', v0=name))
            if file.suffix==".py":compile(file.read_text(encoding="utf-8"),name,"exec")
            existing=destination/rel
            if existing.is_symlink() or not existing.resolve().is_relative_to(destination):raise RuntimeError(tr('Unsafe installed application path'))
        import ast
        tree=ast.parse((release/"omne_footage_lab.py").read_text(encoding="utf-8"))
        versions=[ast.literal_eval(n.value) for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="VERSION" for t in n.targets)]
        if versions!=[expected_version]:raise RuntimeError(tr('Package version does not match update manifest'))
        validate_ui_profile(json.loads((release/"ui_profile.json").read_text(encoding="utf-8")))
        # Keep one restore point per installation attempt; swap the entry point last.
        backup=backup_root/("application_"+time.strftime("%Y%m%d_%H%M%S")+"_"+uuid.uuid4().hex[:6])
        backup.mkdir(); existed={}; changed=[]
        order=sorted(set(names)-{"omne_footage_lab.py"})+["omne_footage_lab.py"]
        try:
            for name in order:
                dest=destination/name; existed[name]=dest.exists()
                if dest.exists():
                    prior=backup/name; prior.parent.mkdir(parents=True,exist_ok=True); shutil.copy2(dest,prior)
                dest.parent.mkdir(parents=True,exist_ok=True)
                tmp=dest.with_name(dest.name+".update-"+uuid.uuid4().hex[:8])
                shutil.copy2(release/name,tmp); os.replace(tmp,dest); changed.append(name)
        except Exception:
            for name in reversed(changed):
                dest=destination/name
                if existed[name]:shutil.copy2(backup/name,dest)
                else:dest.unlink(missing_ok=True)
            raise
        return backup
    finally:shutil.rmtree(work,ignore_errors=True)


class App(tk.Tk):
    def __init__(self):
        global _ACTIVE_PROFILE, APP, WEBSITE_URL, SUPPORT_URL
        super().__init__()
        self.title(tr('{v0} {v1}', v0=APP, v1=VERSION))
        self.geometry("1380x860")
        self.minsize(860,620)

        self.ev=queue.Queue()
        self.jobs={}
        self.cancels={}
        self.jobq=queue.Queue()
        self.running=None
        self.files=[]

        self.logger=SessionLog()
        self.proc=Processor(lambda **kw:self.ev.put(kw),self.logger,"batch")
        self.preview_proc=Processor(lambda **kw:self.ev.put(kw),self.logger,"preview")
        self.preview_logs=[]
        self.preview_frames=[]
        self.pi=0
        self.playing=False
        self.after_id=None
        self.preview_running=False
        self.preview_cancel=threading.Event()
        self.preview_tmp=Path(tempfile.mkdtemp(prefix="omne-preview."))
        self.current_preview_dir=None
        self.active_preview_token=None

        self.config_dir=user_config_dir()
        self.preferences_path=self.config_dir/"preferences.json"
        self.custom_presets_path=self.config_dir/"custom_presets.json"
        self.config_dir.mkdir(parents=True,exist_ok=True)
        self.custom_presets=self.read_custom_presets()
        self.presets={**PRESETS,**self.custom_presets}
        self.pending_preview_source=""
        self.saved_layout={}
        self.collapsible_manual={}
        self.update_info=None
        self.update_check_running=False
        self.update_install_running=False
        self.startup_window=None
        self.update_install_button=None
        self.ui_profile=load_packaged_ui_profile()
        self.ui_labels=self.ui_profile.get("labels",{})
        self.ui_tooltips=self.ui_profile.get("tooltips",{})
        self.theme_library=copy.deepcopy(self.ui_profile.get("themes",{}))
        self.published_themes=[x for x in self.ui_profile.get("published_themes",[]) if x in self.theme_library]
        self.user_themes=load_user_themes()
        for _name,_chrome in self.user_themes.items():self.theme_library[_name]=copy.deepcopy(_chrome)
        self.available_themes=list(dict.fromkeys(self.published_themes+list(self.user_themes)))
        self.default_theme=self.ui_profile.get("default_theme") if self.ui_profile.get("default_theme") in self.published_themes else (self.published_themes[0] if self.published_themes else "Pungent Purple")
        self.initial_theme_name=self.default_theme
        try:
            if self.preferences_path.exists():
                _pref=json.loads(self.preferences_path.read_text(encoding="utf-8")); _candidate=_pref.get("theme_name")
                if _candidate in self.available_themes:self.initial_theme_name=_candidate
        except Exception:pass
        self.ui_chrome=copy.deepcopy(self.theme_library.get(self.initial_theme_name,self.ui_profile.get("chrome",DEFAULT_CHROME)))
        self.ui_profile["chrome"]=self.ui_chrome
        self.tooltip_instances=[]
        _ACTIVE_PROFILE=self.ui_profile
        APP=self.ui_profile["identity"]["app_name"]
        WEBSITE_URL=self.ui_profile["identity"]["website_url"]
        SUPPORT_URL=self.ui_profile["identity"]["support_url"]
        self.title(self.t("app_title","{app} {version}").format(app=APP,version=VERSION))
        self._layout_clamp_after=None

        self.vars()
        self.ui()
        self.load_history()

        threading.Thread(target=self.worker,daemon=True).start()
        self.poll_after_id=self.after(120,self.poll)
        self.protocol("WM_DELETE_WINDOW",self.close)

        self.load_preferences()
        self.refresh_preset_values()
        self.refresh_summary()
        if Path(self.src.get()).expanduser().exists():self.after(200,self.scan)
        self.layout_after_id=self.after(350,self.restore_layout_sashes)
        self.startup_after_id=self.after(450,self.show_startup_panel) if self.show_startup.get() else None
        self.update_after_id=self.after(900,lambda:self.check_updates(silent=True)) if self.check_updates_var.get() else None

        self.logger.write(f"Python: {platform.python_version()} | {platform.platform()}")
        self.logger.write((f"Preview scaling: Pillow {getattr(PIL, '__version__', 'unknown')} · {_PIL_RESAMPLE_API}") if Image else "Preview scaling: Tk whole-frame fallback (install python3-pil.imagetk for smooth scaling)")
        try:
            ff=subprocess.run([FFMPEG_BIN or "ffmpeg","-version"],capture_output=True,text=True,timeout=5).stdout.splitlines()[0]
            self.logger.write(ff)
        except Exception:pass

    def vars(self):
        self.src=tk.StringVar(value=DEFAULT_UI["source"]); self.out=tk.StringVar(value=DEFAULT_UI["output"]); self.maxm=tk.DoubleVar(value=DEFAULT_UI["max_mib"])
        self.mode=tk.StringVar(value=DEFAULT_UI["mode"]); self.preset=tk.StringVar(value=DEFAULT_UI["preset"])
        self.res=tk.StringVar(value=DEFAULT_UI["resolution"]); self.fps=tk.DoubleVar(value=DEFAULT_UI["fps"])
        self.crf=tk.IntVar(value=DEFAULT_UI["crf"]); self.bitrate=tk.DoubleVar(value=DEFAULT_UI["bitrate"]); self.x264=tk.StringVar(value=DEFAULT_UI["x264"])
        self.generation=tk.IntVar(value=DEFAULT_UI["generation"]); self.scanv=tk.DoubleVar(value=DEFAULT_UI["scan"]); self.interp=tk.BooleanVar(value=DEFAULT_UI["interp"])
        self.interpfps=tk.DoubleVar(value=DEFAULT_UI["interp_fps"]); self.echo=tk.IntVar(value=DEFAULT_UI["echo"]); self.decay=tk.DoubleVar(value=DEFAULT_UI["decay"])
        self.glow=tk.DoubleVar(value=DEFAULT_UI["glow"]); self.chroma=tk.DoubleVar(value=DEFAULT_UI["chroma"]); self.blur=tk.DoubleVar(value=DEFAULT_UI["blur"])
        self.warp=tk.DoubleVar(value=DEFAULT_UI["warp"]); self.sat=tk.DoubleVar(value=DEFAULT_UI["sat"]); self.hue=tk.DoubleVar(value=DEFAULT_UI["hue"])
        self.previewsrc=tk.StringVar(value=DEFAULT_UI["preview_source"]); self.pstart=tk.DoubleVar(value=DEFAULT_UI["preview_start"]); self.plen=tk.DoubleVar(value=DEFAULT_UI["preview_length"])
        self.pstatus=tk.StringVar(value=tr('Preview tests the current glitch settings using a fast proxy.'))
        self.pprog=tk.DoubleVar(value=0)
        self.scanstatus=tk.StringVar(value=tr('No folder scanned'))
        self.qstatus=tk.StringVar(value=tr('Idle'))
        self.summary=tk.StringVar(value="")
        self.show_startup=tk.BooleanVar(value=DEFAULT_UI["show_startup"])
        self.check_updates_var=tk.BooleanVar(value=DEFAULT_UI["check_updates"])
        self.tooltips_enabled_var=tk.BooleanVar(value=DEFAULT_UI["enable_tooltips"])
        self.theme_name=tk.StringVar(value=getattr(self,"initial_theme_name",getattr(self,"default_theme","Pungent Purple")))
        self.update_status=tk.StringVar(value=tr('v{v0} · update check pending', v0=VERSION))

    def t(self,key,default):
        return str(self.ui_labels.get(key,default))

    def add_tip(self,widget,key):
        try:widget._omne_key=key
        except Exception:pass
        if hasattr(self,"widget_catalogue"):
            self.widget_catalogue[key+"."+widget.winfo_class()]={"key":key,"class":widget.winfo_class()}
        try:apply_element_style(widget,key,self.ui_profile)
        except Exception as error:self.logger.write(f"Element style {key}: {error}")
        text=self.ui_tooltips.get(key)
        if text:
            tip=ToolTip(widget,text,self.ui_chrome.get("tooltip_bg","#fff6cf"),self.ui_chrome.get("tooltip_fg","#161616"),self.ui_chrome.get("tooltip_delay_ms",420))
            try:tip.set_enabled(bool(self.tooltips_enabled_var.get()))
            except Exception:pass
            self.tooltip_instances.append(tip)
        return widget

    def make_paned(self,parent,orient,tip_key):
        pane=ResizablePane(parent,orient,self.ui_chrome)
        self.add_tip(pane,tip_key)
        return pane

    def ui(self):
        self.style=configure_theme(self,self.ui_chrome)
        c=self.ui_chrome; pad=c["panel_padding"]
        self.widget_catalogue={};self.collapsible_sections={}
        root=ttk.Frame(self,padding=pad); root.pack(fill="both",expand=True)

        # Source/output is a compact collapsible input bar, not a resizable pane.
        self.source_section=self.make_collapsible(root,"source_output",self.t("source_output","Source / Output"),True)
        self.source_section.pack(fill="x")
        top=self.source_section.body;top.columnconfigure(1,weight=1)
        self.source_label=self.add_tip(ttk.Label(top,text=self.t("camera_folder","Camera folder")),"camera_folder")
        self.source_entry=self.add_tip(ttk.Entry(top,textvariable=self.src,width=36),"camera_folder")
        self.source_browse=self.add_tip(ttk.Button(top,text=self.t("browse_source","Browse"),command=self.browse_src),"browse_source")
        self.scan_button=self.add_tip(ttk.Button(top,text=self.t("scan","Scan"),command=self.scan),"scan")
        self.output_label=self.add_tip(ttk.Label(top,text=self.t("output","Output")),"output")
        self.output_entry=self.add_tip(ttk.Entry(top,textvariable=self.out,width=34),"output")
        self.output_browse=self.add_tip(ttk.Button(top,text=self.t("browse_output","Browse"),command=self.browse_out),"browse_output")
        self.max_label=self.add_tip(ttk.Label(top,text=self.t("max_upload","Max upload MiB")),"max_upload")
        self.max_spin=self.add_tip(ttk.Spinbox(top,from_=4,to=2048,textvariable=self.maxm,width=7,command=self.refresh_summary),"max_upload")
        self.scan_label=self.add_tip(ttk.Label(top,textvariable=self.scanstatus,style="Muted.TLabel",justify="left"),"scan_status");bind_wrap(self.scan_label)
        self.update_bar=ttk.Frame(top)
        self.add_tip(ttk.Label(self.update_bar,textvariable=self.update_status,style="Muted.TLabel"),"updates").pack(side="left",padx=(0,6))
        self.add_tip(ttk.Button(self.update_bar,text=self.t("about_updates","About / Updates…"),command=lambda:self.show_startup_panel(force=True)),"about_updates").pack(side="left")
        top.bind("<Configure>",lambda e:self._layout_source_controls(e.width),add="+")
        self.after_idle(lambda:self._layout_source_controls(top.winfo_width()))

        # The only vertical resize edge in the main window now balances the
        # workspace against the process monitor. Compact input rows collapse.
        self.main_panes=self.make_paned(root,tk.VERTICAL,"resize_outer");self.outer_panes=self.main_panes
        self.main_panes.pack(fill="both",expand=True,pady=(4,0))
        self.workspace_region=ttk.Frame(self.main_panes);self.jobs_region=ttk.Frame(self.main_panes)
        self.main_panes.add(self.workspace_region,minsize=300);self.main_panes.add(self.jobs_region,minsize=145)

        self.workspace_panes=self.make_paned(self.workspace_region,tk.HORIZONTAL,"resize_workspace");self.workspace_panes.pack(fill="both",expand=True)
        left=ttk.Frame(self.workspace_panes);right=ttk.Frame(self.workspace_panes)
        self.workspace_panes.add(left,minsize=270);self.workspace_panes.add(right,minsize=320)

        self.operation_section=self.make_collapsible(left,"operation",self.t("operation","Operation"),True)
        self.operation_section.pack(fill="x",pady=(0,4))
        op=self.operation_section.body
        self.inspector_heading=self.add_tip(ttk.Label(op,text=self.t("inspector","Inspector"),style="Title.TLabel"),"inspector")
        self.lossless_radio=self.add_tip(ttk.Radiobutton(op,text=self.t("lossless","Lossless minimal clips"),variable=self.mode,value="lossless",command=self.mode_changed),"lossless")
        self.glitch_radio=self.add_tip(ttk.Radiobutton(op,text=self.t("glitch_derivative","Glitch derivative"),variable=self.mode,value="glitch",command=self.mode_changed),"glitch_derivative")
        self.summary_label=self.add_tip(ttk.Label(op,textvariable=self.summary,justify="left",style="Muted.TLabel"),"operation_summary");bind_wrap(self.summary_label)
        op.bind("<Configure>",lambda e:self._layout_operation_controls(e.width),add="+")
        self.after_idle(lambda:self._layout_operation_controls(op.winfo_width()))

        controls_region=ttk.Frame(left);controls_region.pack(fill="both",expand=True)
        self.nb=self.add_tip(ttk.Notebook(controls_region),"inspector_tabs")
        self.format_scroll=self.scroll_section(self.nb,"format_tab",height=200)
        self.glitch_scroll=self.scroll_section(self.nb,"glitch_tab",height=220)
        self.nb.add(self.format_scroll,text=self.t("format_tab","Format"));self.nb.add(self.glitch_scroll,text=self.t("glitch_tab","Glitch"))
        fmt=ttk.Frame(self.format_scroll.body,padding=pad);fx=ttk.Frame(self.glitch_scroll.body,padding=pad)
        fmt.pack(fill="both",expand=True);fx.pack(fill="both",expand=True);fmt.columnconfigure(1,weight=1);fx.columnconfigure(1,weight=1)
        format_help=self.add_tip(ttk.Label(fmt,text=self.t("format_help","Glitch outputs only. Lossless mode preserves the camera streams."),justify="left"),"format_tab");format_help.grid(row=0,column=0,columnspan=2,sticky="ew",pady=(0,6));bind_wrap(format_help)
        self.combo(fmt,1,"resolution","Resolution",self.res,["Source","1280x720","960x540","640x360","426x240"])
        self.combo(fmt,2,"fps","FPS",self.fps,[59.94,29.97,24,15,12])
        self.spin(fmt,3,"crf","CRF",self.crf,10,40,1);self.spin(fmt,4,"max_bitrate","Max bitrate Mbps",self.bitrate,.25,20,.25)
        self.combo(fmt,5,"x264","x264",self.x264,["ultrafast","superfast","veryfast","faster","fast","medium"])
        self.preset_display=tk.StringVar(value=self.display_preset(self.preset.get()))
        self.preset_combo=self.combo(fx,0,"preset","Preset",self.preset_display,[self.display_preset(x) for x in self.preset_names()]);self.preset_combo.bind("<<ComboboxSelected>>",self.select_display_preset)
        self.preset.trace_add("write",lambda *_:self.preset_display.set(self.display_preset(self.preset.get())))
        pa=ttk.Frame(fx);pa.grid(row=1,column=0,columnspan=2,sticky="ew",pady=4);pa.columnconfigure(1,weight=1)
        self.add_tip(ttk.Button(pa,text=self.t("save_preset","Save Current as Preset…"),command=self.save_custom_preset),"save_preset").grid(row=0,column=0,sticky="w")
        ph=self.add_tip(ttk.Label(pa,text=self.t("preset_help","Custom presets are saved locally."),style="Muted.TLabel",justify="left"),"preset_help");ph.grid(row=0,column=1,sticky="ew",padx=6);bind_wrap(ph)
        self.spin(fx,2,"generation_passes","Generation passes",self.generation,0,4,1)
        r=3;r=self.scale(fx,r,"scan_strength","Scan strength",self.scanv,0,.8,.01)
        self.add_tip(ttk.Checkbutton(fx,text=self.t("motion_interpolation","Motion interpolation"),variable=self.interp,command=self.refresh_summary),"motion_interpolation").grid(row=r,column=0,columnspan=2,sticky="w");r+=1
        self.spin(fx,r,"interpolation_source_fps","Interpolation source FPS",self.interpfps,4,30,1);r+=1
        self.spin(fx,r,"echo_frames","Echo frames",self.echo,1,10,1);r+=1
        for key,name,var,a,b,res in [("echo_decay","Echo decay",self.decay,.05,.9,.01),("afterglow","Afterglow",self.glow,0,.995,.005),("chroma_shift","Chroma shift",self.chroma,0,12,.25),("blur","Blur",self.blur,0,4,.05),("liquid_warp","Liquid warp",self.warp,0,18,.25),("saturation","Saturation",self.sat,.4,2,.01),("hue_drift","Hue drift",self.hue,0,8,.05)]:
            r=self.scale(fx,r,key,name,var,a,b,res)
        self.nb.pack(fill="both",expand=True)
        self.apply_bar=ttk.Frame(controls_region);self.apply_bar.pack(fill="x",pady=(4,0))
        self.apply_folder_btn=self.add_tip(ttk.Button(self.apply_bar,text=self.t("apply_folder","Apply Folder"),command=self.enqueue_all),"apply_folder")
        self.apply_selected_btn=self.add_tip(ttk.Button(self.apply_bar,text=self.t("apply_selected","Apply Selected"),command=self.enqueue_one),"apply_selected")
        self.reset_button=self.add_tip(ttk.Button(self.apply_bar,text=self.t("reset_defaults","Reset Defaults"),command=self.reset_defaults),"reset_defaults")
        self.apply_bar.bind("<Configure>",lambda e:self._layout_apply_actions(e.width),add="+")
        self.after_idle(lambda:self._layout_apply_actions(self.apply_bar.winfo_width()))

        self.preview_section=self.make_collapsible(right,"preview_controls",self.t("preview","Preview"),True)
        self.preview_section.pack(fill="x",pady=(0,4))
        pc=self.preview_section.body
        self.preview_help=self.add_tip(ttk.Label(pc,text=self.t("preview_help","Fast proxy for tuning; final output uses the Inspector format."),style="Muted.TLabel",justify="left"),"preview_help");bind_wrap(self.preview_help)
        self.preview_source_label=self.add_tip(ttk.Label(pc,text=self.t("source","Source")),"source")
        self.pscombo=self.add_tip(ttk.Combobox(pc,textvariable=self.previewsrc,state="readonly",width=28),"source");self.pscombo.bind("<<ComboboxSelected>>",lambda e:self.preview_source_info())
        self.render_button=self.add_tip(ttk.Button(pc,text=self.t("render_preview","Render Preview"),command=self.preview),"render_preview")
        self.cancel_preview_button=self.add_tip(ttk.Button(pc,text=self.t("cancel_preview","Cancel Preview"),command=self.cancel_preview),"cancel_preview")
        self.play_button=self.add_tip(ttk.Button(pc,text=self.t("play_pause","Play / Pause"),command=self.toggle),"play_pause")
        self.start_label=self.add_tip(ttk.Label(pc,text=self.t("start","Start")),"start")
        self.start_spin=self.add_tip(ttk.Spinbox(pc,from_=0,to=99999,textvariable=self.pstart,width=6),"start")
        self.length_label=self.add_tip(ttk.Label(pc,text=self.t("length","Length")),"length")
        self.length_spin=self.add_tip(ttk.Spinbox(pc,from_=2,to=12,textvariable=self.plen,width=5),"length")
        pc.bind("<Configure>",lambda e:self._layout_preview_controls(e.width),add="+")
        self.after_idle(lambda:self._layout_preview_controls(pc.winfo_width()))

        preview_body=ttk.Frame(right);preview_body.pack(fill="both",expand=True)
        self.image=self.add_tip(FitPreview(preview_body,c),"preview_visual");self.image.pack(fill="both",expand=True);self.image.configure(text=self.t("preview_empty","Render a short test clip"))
        self.add_tip(ttk.Progressbar(preview_body,variable=self.pprog,maximum=1),"preview_progress").pack(fill="x",pady=(4,0))
        self.preview_status_label=self.add_tip(ttk.Label(preview_body,textvariable=self.pstatus,style="Muted.TLabel",justify="left"),"preview_status");self.preview_status_label.pack(fill="x",pady=(3,0));bind_wrap(self.preview_status_label)

        jobs=ttk.LabelFrame(self.jobs_region,text=self.t("processes","Processes"),padding=4);jobs.pack(fill="both",expand=True)
        table=ttk.Frame(jobs);table.rowconfigure(0,weight=1);table.columnconfigure(0,weight=1)
        self.tree=self.add_tip(ttk.Treeview(table,columns=("src","op","status","progress","msg"),show="headings",height=5,selectmode="browse"),"processes")
        for col,key,width in [("src","source",235),("op","operation",135),("status","status",92),("progress","progress",72),("msg","stage_result",420)]:
            self.tree.heading(col,text=self.t(key,DEFAULT_LABELS.get(key,key)));self.tree.column(col,width=width,minwidth=48 if col!="msg" else 90,anchor="w",stretch=True)
        for state,token in [("failed","failure_fg"),("completed","success_fg"),("running","running_fg")]:self.tree.tag_configure(state,foreground=c[token])
        self.tree.grid(row=0,column=0,sticky="nsew");vs=self.add_tip(AutoScrollbar(table,orient="vertical",command=self.tree.yview),"scroll_vertical");vs.grid(row=0,column=1,sticky="ns");self.tree.configure(yscrollcommand=vs.set);table.pack(fill="both",expand=True)
        self.jobs_action_bar=ttk.Frame(jobs);self.jobs_action_bar.pack(side="bottom",fill="x",pady=(4,0))
        action_specs=[("retry","Retry",self.retry),("repair_retry","Repair + Retry",self.repair),("cancel_running","Cancel Running",self.cancel),("open_output","Open Output",self.openout),("diagnostics","Diagnostics…",self.show_diagnostics),("copy_job_log","Copy Job Log",self.copy_job_log),("open_logs","Open Logs",self.open_logs)]
        self.job_action_widgets=[]
        for key,label,cmd in action_specs:self.job_action_widgets.append(self.add_tip(ttk.Button(self.jobs_action_bar,text=self.t(key,label),command=cmd),key))
        self.queue_label=self.add_tip(ttk.Label(self.jobs_action_bar,textvariable=self.qstatus,style="Muted.TLabel",justify="left"),"queue_status");bind_wrap(self.queue_label)
        self.jobs_action_bar.bind("<Configure>",lambda e:self._layout_job_actions(e.width),add="+")
        self.after_idle(lambda:self._layout_job_actions(self.jobs_action_bar.winfo_width()))

        self.main_panes.set_bounds_provider(self._main_sash_bounds)
        self.workspace_panes.set_bounds_provider(self._workspace_sash_bounds)
        for pane in (self.main_panes,self.workspace_panes):pane.bind("<<OmneSashChanged>>",lambda _e:self.after(50,self.save_layout_sashes),add="+")
        self.bind("<Configure>",self.on_window_configure,add="+")
        install_wheel_router(self)

    def make_collapsible(self,parent,key,title,expanded=True):
        section=CollapsibleSection(parent,title,expanded=expanded,on_toggle=lambda value,k=key:self._manual_collapsible(k,value))
        self.collapsible_sections[key]=section;self.add_tip(section.header,key);return section

    def _manual_collapsible(self,key,expanded):
        self.collapsible_manual[key]=bool(expanded);self.save_preferences(silent=True)

    def _grid_clear(self,widgets):
        for widget in widgets:
            try:widget.grid_forget()
            except Exception:pass

    def _layout_source_controls(self,width):
        widgets=[self.source_label,self.source_entry,self.source_browse,self.scan_button,self.output_label,self.output_entry,self.output_browse,self.max_label,self.max_spin,self.scan_label,self.update_bar]
        self._grid_clear(widgets);top=self.source_section.body
        for col in range(10):top.columnconfigure(col,weight=0)
        if width>=1180:
            top.columnconfigure(1,weight=1);top.columnconfigure(5,weight=1)
            self.source_label.grid(row=0,column=0,sticky="w",padx=(0,4),pady=2);self.source_entry.grid(row=0,column=1,sticky="ew",padx=(0,4),pady=2);self.source_browse.grid(row=0,column=2,padx=2,pady=2);self.scan_button.grid(row=0,column=3,padx=(2,10),pady=2)
            self.output_label.grid(row=0,column=4,sticky="w",padx=(0,4),pady=2);self.output_entry.grid(row=0,column=5,sticky="ew",padx=(0,4),pady=2);self.output_browse.grid(row=0,column=6,padx=2,pady=2);self.max_label.grid(row=0,column=7,padx=(10,4),pady=2);self.max_spin.grid(row=0,column=8,sticky="w",pady=2)
            self.scan_label.grid(row=1,column=0,columnspan=6,sticky="ew",pady=(2,0));self.update_bar.grid(row=1,column=6,columnspan=3,sticky="e",pady=(2,0))
        else:
            top.columnconfigure(1,weight=1)
            self.source_label.grid(row=0,column=0,sticky="w",padx=(0,4),pady=2);self.source_entry.grid(row=0,column=1,sticky="ew",padx=(0,4),pady=2);self.source_browse.grid(row=0,column=2,padx=2,pady=2);self.scan_button.grid(row=0,column=3,padx=2,pady=2)
            self.output_label.grid(row=1,column=0,sticky="w",padx=(0,4),pady=2);self.output_entry.grid(row=1,column=1,sticky="ew",padx=(0,4),pady=2);self.output_browse.grid(row=1,column=2,padx=2,pady=2);self.max_label.grid(row=1,column=3,padx=(8,4),pady=2);self.max_spin.grid(row=1,column=4,sticky="w",pady=2)
            self.scan_label.grid(row=2,column=0,columnspan=3,sticky="ew",pady=(2,0));self.update_bar.grid(row=2,column=3,columnspan=2,sticky="e",pady=(2,0))

    def _layout_operation_controls(self,width):
        self._grid_clear([self.inspector_heading,self.lossless_radio,self.glitch_radio,self.summary_label]);op=self.operation_section.body
        for c in range(3):op.columnconfigure(c,weight=0)
        if width>=520:
            op.columnconfigure(2,weight=1);self.inspector_heading.grid(row=0,column=0,sticky="w",padx=(0,8));self.lossless_radio.grid(row=0,column=1,sticky="w",padx=(0,8));self.glitch_radio.grid(row=0,column=2,sticky="w");self.summary_label.grid(row=1,column=0,columnspan=3,sticky="ew",pady=(3,0))
        else:
            op.columnconfigure(0,weight=1);self.inspector_heading.grid(row=0,column=0,sticky="w");self.lossless_radio.grid(row=1,column=0,sticky="w");self.glitch_radio.grid(row=2,column=0,sticky="w");self.summary_label.grid(row=3,column=0,sticky="ew",pady=(3,0))

    def _layout_apply_actions(self,width):
        self._grid_clear([self.apply_folder_btn,self.apply_selected_btn,self.reset_button]);bar=self.apply_bar
        for c in range(3):bar.columnconfigure(c,weight=0)
        if width>=430:
            for c in range(3):bar.columnconfigure(c,weight=1,uniform="apply")
            self.apply_folder_btn.grid(row=0,column=0,sticky="ew",padx=(0,2));self.apply_selected_btn.grid(row=0,column=1,sticky="ew",padx=2);self.reset_button.grid(row=0,column=2,sticky="ew",padx=(2,0))
        else:
            for c in range(2):bar.columnconfigure(c,weight=1,uniform="apply")
            self.apply_folder_btn.grid(row=0,column=0,sticky="ew",padx=(0,2),pady=2);self.apply_selected_btn.grid(row=0,column=1,sticky="ew",padx=(2,0),pady=2);self.reset_button.grid(row=1,column=0,columnspan=2,sticky="ew",pady=2)

    def _layout_preview_controls(self,width):
        widgets=[self.preview_help,self.preview_source_label,self.pscombo,self.render_button,self.cancel_preview_button,self.play_button,self.start_label,self.start_spin,self.length_label,self.length_spin]
        self._grid_clear(widgets);pc=self.preview_section.body
        for c in range(8):pc.columnconfigure(c,weight=0)
        pc.columnconfigure(1,weight=1);self.preview_help.grid(row=0,column=0,columnspan=8,sticky="ew",pady=(0,4))
        self.preview_source_label.grid(row=1,column=0,sticky="w",padx=(0,4));self.pscombo.grid(row=1,column=1,sticky="ew",padx=(0,5))
        if width>=780:
            self.render_button.grid(row=1,column=2,padx=2);self.cancel_preview_button.grid(row=1,column=3,padx=2);self.play_button.grid(row=1,column=4,padx=2);self.start_label.grid(row=1,column=5,padx=(9,2));self.start_spin.grid(row=1,column=6);self.length_label.grid(row=1,column=7,padx=(8,2));self.length_spin.grid(row=1,column=8)
        else:
            self.render_button.grid(row=2,column=0,columnspan=2,sticky="ew",padx=(0,2),pady=(4,2));self.cancel_preview_button.grid(row=2,column=2,columnspan=2,sticky="ew",padx=2,pady=(4,2));self.play_button.grid(row=2,column=4,columnspan=2,sticky="ew",padx=2,pady=(4,2));self.start_label.grid(row=3,column=0,sticky="w",pady=2);self.start_spin.grid(row=3,column=1,sticky="w",pady=2);self.length_label.grid(row=3,column=2,sticky="e",pady=2);self.length_spin.grid(row=3,column=3,sticky="w",padx=(3,0),pady=2)

    def _layout_job_actions(self,width):
        self._grid_clear(self.job_action_widgets+[self.queue_label]);bar=self.jobs_action_bar
        cols=7 if width>=1050 else (4 if width>=650 else 3)
        for c in range(7):bar.columnconfigure(c,weight=1 if c<cols else 0,uniform="jobs" if c<cols else "")
        for i,w in enumerate(self.job_action_widgets):w.grid(row=i//cols,column=i%cols,sticky="ew",padx=2,pady=2)
        rows=(len(self.job_action_widgets)+cols-1)//cols;self.queue_label.grid(row=rows,column=0,columnspan=cols,sticky="ew",padx=3,pady=(3,0))

    def scroll_section(self,parent,key,height=100):
        section=ScrollSection(parent,height=height,chrome=self.ui_chrome);self.add_tip(section.vbar,"scroll_vertical");self.add_tip(section,key);apply_element_style(section.body,key,self.ui_profile)
        override=self.ui_profile.get("elements",{}).get(key+".TFrame",{})
        if override.get("background"):section.canvas.configure(background=override["background"])
        return section

    def display_preset(self,name):
        return self.t("preset."+name,name) if name in PRESETS else name

    def select_display_preset(self,event=None):
        index=self.preset_combo.current()
        names=self.preset_names()
        if 0<=index<len(names):self.preset.set(names[index]); self.use_preset()

    def display_state(self,state):
        return self.t("state."+state,state)

    def queue_layout_clamp(self):
        if self._layout_clamp_after is None:self._layout_clamp_after=self.after(30,self._clamp_after_resize)

    def combo(self,p,r,key,default,v,vals):
        label=self.add_tip(ttk.Label(p,text=self.t(key,default)),key);label.grid(row=r,column=0,sticky="w",pady=3)
        c=self.add_tip(ttk.Combobox(p,textvariable=v,values=vals,state="readonly"),key);c.grid(row=r,column=1,sticky="ew",pady=3);return c

    def spin(self,p,r,key,default,v,a,b,i):
        self.add_tip(ttk.Label(p,text=self.t(key,default)),key).grid(row=r,column=0,sticky="w",pady=3)
        self.add_tip(ttk.Spinbox(p,from_=a,to=b,increment=i,textvariable=v,width=9,command=self.refresh_summary),key).grid(row=r,column=1,sticky="ew",pady=3)

    def scale(self,p,r,key,default,v,a,b,res):
        f=ttk.Frame(p);f.grid(row=r,column=0,columnspan=2,sticky="ew");f.columnconfigure(1,weight=1)
        self.add_tip(ttk.Label(f,text=self.t(key,default)),key).grid(row=0,column=0,sticky="w")
        sc=self.add_tip(tk.Scale(f,from_=a,to=b,resolution=res,variable=v,orient="horizontal",length=self.ui_chrome["slider_length"],bg=self.ui_chrome["scale_bg"],fg=self.ui_chrome["foreground"],troughcolor=self.ui_chrome["scale_trough"],activebackground=self.ui_chrome["active_bg"],highlightthickness=0,command=lambda _x:self.refresh_summary()),key);sc.grid(row=0,column=1,sticky="ew")
        return r+1

    def _clamp(self,value,low,high):return max(low,min(high,value))

    def _main_sash_bounds(self,index):
        h=max(1,self.main_panes.winfo_height());sw=int(self.ui_chrome.get("sash_width",7))
        jobs_min=145;jobs_max=max(220,min(360,len(self.jobs)*int(self.ui_chrome.get("row_height",25))+150))
        lo=max(300,h-jobs_max-sw);hi=max(lo,h-jobs_min-sw)
        return lo,hi

    def _workspace_sash_bounds(self,index):
        w=max(1,self.workspace_panes.winfo_width());sw=int(self.ui_chrome.get("sash_width",7))
        lo=270;hi=max(lo,w-320-sw);return lo,hi

    def clamp_layout_sashes(self):
        try:
            if self.main_panes.winfo_height()>1:
                lo,hi=self._main_sash_bounds(0);self.main_panes.sashpos(0,max(lo,min(hi,self.main_panes.sashpos(0))))
            if self.workspace_panes.winfo_width()>1:
                lo,hi=self._workspace_sash_bounds(0);self.workspace_panes.sashpos(0,max(lo,min(hi,self.workspace_panes.sashpos(0))))
            self.auto_manage_collapsibles()
        except tk.TclError:pass

    def auto_manage_collapsibles(self):
        # Manual user choices win. Otherwise compact sections adapt to available
        # height so essential controls stay visible without an internal scroll.
        h=max(1,self.winfo_height())
        try:workspace_h=max(1,self.workspace_region.winfo_height())
        except Exception:workspace_h=max(1,h-220)
        defaults={"source_output":h>=650,"operation":workspace_h>=360,"preview_controls":workspace_h>=380}
        for key,section in getattr(self,"collapsible_sections",{}).items():
            if key in self.collapsible_manual:section.set_expanded(bool(self.collapsible_manual[key]),notify=False)
            else:section.set_expanded(defaults.get(key,True),notify=False)

    def on_window_configure(self,event=None):
        if event is not None and event.widget is not self:return
        self.auto_manage_collapsibles();self.queue_layout_clamp()
        try:
            self._layout_source_controls(self.source_section.body.winfo_width())
            self._layout_operation_controls(self.operation_section.body.winfo_width())
            self._layout_apply_actions(self.apply_bar.winfo_width())
            self._layout_preview_controls(self.preview_section.body.winfo_width())
            self._layout_job_actions(self.jobs_action_bar.winfo_width())
        except Exception:pass

    def _clamp_after_resize(self):
        self._layout_clamp_after=None;self.clamp_layout_sashes()

    def save_layout_sashes(self):
        try:
            self.clamp_layout_sashes()
            self.saved_layout={"layout_revision":3,"window_geometry":self.geometry(),"main":[self.main_panes.sashpos(0)],"workspace":[self.workspace_panes.sashpos(0)]}
            self.save_preferences(silent=True)
        except Exception as e:self.logger.write(f"Layout save failed: {e}")

    def restore_layout_sashes(self):
        try:
            self.update_idletasks();layout=self.saved_layout if isinstance(self.saved_layout,dict) else {};h=self.main_panes.winfo_height();w=self.workspace_panes.winfo_width()
            if layout.get("layout_revision")==3:
                self.main_panes.sashpos(0,int(layout.get("main",[max(300,h-220)])[0]));self.workspace_panes.sashpos(0,int(layout.get("workspace",[max(300,int(w*.34))])[0]))
            else:
                # Migrate the useful workspace split from pre-v0.2.6 layouts.
                old_workspace=layout.get("workspace",[max(300,int(w*.34))]) if isinstance(layout,dict) else [max(300,int(w*.34))]
                self.main_panes.sashpos(0,max(300,h-220));self.workspace_panes.sashpos(0,int(old_workspace[0]))
            self.auto_manage_collapsibles();self.clamp_layout_sashes()
        except Exception as e:self.logger.write(f"Layout restore failed: {e}")

    def apply_theme(self,name,save=True,chrome_override=None):
        if chrome_override is None:
            if name not in self.theme_library:return
            chrome=copy.deepcopy(self.theme_library[name])
            self.theme_name.set(name)
        else:
            chrome={**copy.deepcopy(DEFAULT_CHROME),**copy.deepcopy(chrome_override)}
        self.ui_chrome=chrome; self.ui_profile["chrome"]=self.ui_chrome
        global _ACTIVE_PROFILE; _ACTIVE_PROFILE=self.ui_profile
        configure_theme(self,self.ui_chrome)
        def walk(widget):
            try:
                key=getattr(widget,"_omne_key",None)
                if key:apply_element_style(widget,key,self.ui_profile)
                if isinstance(widget,ResizablePane):
                    widget.configure(bg=self.ui_chrome["sash_color"],sashwidth=self.ui_chrome["sash_width"],handlesize=self.ui_chrome["handle_size"],handlepad=self.ui_chrome["handle_offset"])
                elif isinstance(widget,ScrollSection):
                    widget.chrome=self.ui_chrome;widget.canvas.configure(background=self.ui_chrome["background"])
                elif isinstance(widget,tk.Scale):
                    widget.configure(bg=self.ui_chrome["scale_bg"],fg=self.ui_chrome["foreground"],troughcolor=self.ui_chrome["scale_trough"],activebackground=self.ui_chrome["active_bg"],length=self.ui_chrome["slider_length"])
                elif isinstance(widget,tk.Text):
                    widget.configure(bg=self.ui_chrome["field_bg"],fg=self.ui_chrome["field_fg"],insertbackground=self.ui_chrome["accent"],selectbackground=self.ui_chrome["selection_bg"],selectforeground=self.ui_chrome["selection_fg"],font=(self.ui_chrome["mono_font"],self.ui_chrome["mono_size"]))
                elif isinstance(widget,tk.Listbox):
                    widget.configure(bg=self.ui_chrome["field_bg"],fg=self.ui_chrome["field_fg"],selectbackground=self.ui_chrome["selection_bg"],selectforeground=self.ui_chrome["selection_fg"])
            except Exception as error:self.logger.write(f"Theme refresh {widget}: {error}")
            for child in widget.winfo_children():walk(child)
        walk(self)
        for tip in self.tooltip_instances:
            tip.bg=self.ui_chrome["tooltip_bg"];tip.fg=self.ui_chrome["tooltip_fg"];tip.delay=self.ui_chrome["tooltip_delay_ms"]
        try:
            self.tree.tag_configure("failed",foreground=self.ui_chrome["failure_fg"])
            self.tree.tag_configure("completed",foreground=self.ui_chrome["success_fg"])
            self.tree.tag_configure("running",foreground=self.ui_chrome["running_fg"])
        except Exception:pass
        try:
            if getattr(self,"image",None) and isinstance(self.image,FitPreview):self.image.set_chrome(self.ui_chrome)
        except Exception:pass
        try:
            if self.startup_window and self.startup_window.winfo_exists():self.startup_window.configure(background=self.ui_chrome["background"])
        except Exception:pass
        if save and chrome_override is None:self.save_preferences(silent=True)

    def refresh_theme_choices(self):
        self.available_themes=list(dict.fromkeys(self.published_themes+list(self.user_themes)))
        if getattr(self,"theme_combo",None):
            try:self.theme_combo.configure(values=self.available_themes)
            except Exception:pass

    def set_tooltips_enabled(self,save=True):
        enabled=bool(self.tooltips_enabled_var.get())
        for tip in self.tooltip_instances:
            try:tip.set_enabled(enabled)
            except Exception:pass
        if save:self.save_preferences(silent=True)

    def open_user_theme_studio(self):
        UserThemeStudio(self)

    def show_startup_panel(self,force=False):
        if self.startup_window and self.startup_window.winfo_exists():
            self.startup_window.deiconify(); self.startup_window.lift(); return
        if not force and not self.show_startup.get():return
        win=tk.Toplevel(self); self.startup_window=win
        win.title(self.t("welcome_title","{app} · Welcome").format(app=APP)); win.transient(self)
        body=ttk.Frame(win,padding=18); body.pack(fill="both",expand=True); body.columnconfigure(0,weight=1)

        # Compact two-column intro: identity/actions on the left, Quick Use on the right.
        intro=ttk.Frame(body); intro.grid(row=0,column=0,sticky="ew"); intro.columnconfigure(0,weight=3); intro.columnconfigure(1,weight=2)
        left=ttk.Frame(intro); left.grid(row=0,column=0,sticky="nsew",padx=(0,14))
        self.add_tip(ttk.Label(left,text=self.t("welcome_heading","{app}").format(app=APP),style="Welcome.TLabel"),"welcome_heading").pack(anchor="w")
        self.add_tip(ttk.Label(left,text=self.t("welcome_version","Prototype release v{version}").format(version=VERSION)),"welcome_version").pack(anchor="w",pady=(1,6))
        desc=self.add_tip(ttk.Label(left,text=self.t("welcome_description","Prepare camera footage for OmN-e Waves."),wraplength=390,justify="left"),"welcome_description"); desc.pack(anchor="w",fill="x")
        links=ttk.Frame(left); links.pack(fill="x",pady=(10,0))
        self.add_tip(ttk.Button(links,text=self.t("visit_site","Visit omne.space"),command=lambda:webbrowser.open(WEBSITE_URL)),"visit_site").pack(side="left")
        self.add_tip(ttk.Button(links,text=self.t("support","Support / Donate"),command=lambda:webbrowser.open(SUPPORT_URL)),"support").pack(side="left",padx=8)

        quick=self.add_tip(ttk.LabelFrame(intro,text=self.t("quick_use_title","Quick Use"),padding=(10,8)),"quick_use")
        quick.grid(row=0,column=1,sticky="nsew")
        quick_text=self.add_tip(ttk.Label(quick,text=self.t("quick_use_body","1. Choose folders + Scan.\n2. Pick Lossless or Glitch.\n3. Preview/tune one clip.\n4. Apply Selected or Folder."),justify="left",anchor="nw",wraplength=260),"quick_use")
        quick_text.pack(fill="both",expand=True)

        update=self.add_tip(ttk.LabelFrame(body,text=self.t("updates","Updates"),padding=9),"updates"); update.grid(row=1,column=0,sticky="ew",pady=(12,6))
        self.add_tip(ttk.Label(update,textvariable=self.update_status),"update_status").pack(anchor="w")
        self.update_notes_label=self.add_tip(ttk.Label(update,text="",wraplength=650,justify="left"),"release_notes"); self.update_notes_label.pack(anchor="w",fill="x",pady=3)
        ub=ttk.Frame(update); ub.pack(fill="x",pady=4)
        self.add_tip(ttk.Button(ub,text=self.t("check_now","Check Now"),command=lambda:self.check_updates(silent=False)),"check_now").pack(side="left")
        self.update_install_button=self.add_tip(ttk.Button(ub,text=self.t("download_install","Download & Install"),command=self.install_update,state="disabled"),"download_install"); self.update_install_button.pack(side="left",padx=6)

        theme_row=ttk.Frame(body); theme_row.grid(row=2,column=0,sticky="ew",pady=(8,5)); theme_row.columnconfigure(4,weight=1)
        self.add_tip(ttk.Label(theme_row,text=self.t("theme","Theme")),"theme").grid(row=0,column=0,sticky="w")
        theme_combo=self.add_tip(ttk.Combobox(theme_row,textvariable=self.theme_name,values=self.available_themes,state="readonly",width=24),"theme"); theme_combo.grid(row=0,column=1,sticky="w",padx=8); self.theme_combo=theme_combo
        theme_combo.bind("<<ComboboxSelected>>",lambda _e:self.apply_theme(self.theme_name.get(),save=True))
        self.add_tip(ttk.Button(theme_row,text=self.t("customize_theme","Customize…"),command=self.open_user_theme_studio),"customize_theme").grid(row=0,column=2,sticky="w",padx=(0,8))
        self.add_tip(ttk.Label(theme_row,text=self.t("theme_help","Choose a published or locally saved interface theme."),style="Muted.TLabel",wraplength=280,justify="left"),"theme").grid(row=0,column=4,sticky="w")

        toggles=ttk.Frame(body); toggles.grid(row=3,column=0,sticky="ew",pady=(2,0))
        self.add_tip(ttk.Checkbutton(toggles,text=self.t("check_updates_startup","Check for updates whenever the app opens"),variable=self.check_updates_var,command=lambda:self.save_preferences(silent=True)),"check_updates_startup").pack(anchor="w")
        self.add_tip(ttk.Checkbutton(toggles,text=self.t("enable_tooltips","Enable explanatory tooltips"),variable=self.tooltips_enabled_var,command=lambda:self.set_tooltips_enabled(save=True)),"enable_tooltips").pack(anchor="w")
        self.add_tip(ttk.Checkbutton(toggles,text=self.t("show_welcome","Show this welcome panel on startup"),variable=self.show_startup,command=lambda:self.save_preferences(silent=True)),"show_welcome").pack(anchor="w")

        def close_panel():
            win.destroy(); self.startup_window=None; self.update_install_button=None; self.update_notes_label=None
        self.add_tip(ttk.Button(body,text=self.t("continue","Continue"),command=close_panel),"continue").grid(row=4,column=0,sticky="e",pady=(8,0))
        win.protocol("WM_DELETE_WINDOW",close_panel)
        win.update_idletasks(); reqw=max(760,body.winfo_reqwidth()+36); reqh=max(455,body.winfo_reqheight()+36)
        sw=win.winfo_screenwidth(); sh=win.winfo_screenheight(); reqw=min(reqw,sw-80); reqh=min(reqh,sh-80)
        x=max(0,(sw-reqw)//2); y=max(0,(sh-reqh)//3); win.geometry(f"{reqw}x{reqh}+{x}+{y}"); win.resizable(False,False)
        self.refresh_update_panel()


    def refresh_update_panel(self):
        if not self.update_install_button:return
        info=self.update_info or {}
        available=bool(info.get("available")) and bool(info.get("asset"))
        try:self.update_install_button.configure(state="normal" if available and not self.update_install_running else "disabled")
        except Exception:pass
        notes=str(info.get("notes") or "")
        if getattr(self,"update_notes_label",None):
            try:self.update_notes_label.configure(text=notes)
            except Exception:pass

    def check_updates(self,silent=True):
        if self.update_check_running:return
        self.update_check_running=True; self.update_status.set(tr('Checking omne.space for updates…'))
        self.refresh_update_panel()
        def work():
            try:
                req=urllib.request.Request(UPDATE_MANIFEST_URL,headers={"User-Agent":f"OmN-e-Footage-Lab/{VERSION}"})
                with trusted_open(UPDATE_MANIFEST_URL,timeout=8) as response:
                    raw=response.read(1024*1024+1)
                    if len(raw)>1024*1024:raise RuntimeError(tr('Update manifest too large'))
                    data=json.loads(raw.decode("utf-8"))
                if not isinstance(data,dict) or not data.get("version"):raise RuntimeError(tr('Invalid update manifest'))
                newest=str(data["version"]); available=version_key(newest)>version_key(VERSION)
                assets=data.get("assets",{}) if isinstance(data.get("assets",{}),dict) else {}
                key=update_platform_key()
                asset=(assets.get(key) or assets.get(update_platform_fallback(key))) if available else None
                self.ev.put(dict(update_result=True,manifest=data,available=available,asset=asset,silent=silent))
            except Exception as e:self.ev.put(dict(update_error=str(e),silent=silent))
        threading.Thread(target=work,daemon=True).start()

    def _trusted_update_url(self,url):
        parsed=urllib.parse.urlparse(str(url))
        host=(parsed.hostname or "").lower()
        return parsed.scheme=="https" and (host=="omne.space" or host.endswith(".omne.space"))

    def install_update(self):
        if self.update_install_running:return
        if self.running or self.preview_running or any(j.status=="queued" for j in self.jobs.values()):
            messagebox.showinfo(APP,tr('Finish or cancel the preview and queued conversions before installing an update.'),parent=self); return
        info=copy.deepcopy(self.update_info or {}); asset=info.get("asset") or {}
        url=str(asset.get("url") or ""); expected=str(asset.get("sha256") or "").lower().strip()
        kind=str(asset.get("kind") or "zip-source")
        if not re.fullmatch(r"[0-9a-f]{64}",expected) or not trusted_download_url(url):
            messagebox.showerror(APP,tr('The update package URL or SHA-256 checksum is invalid.'),parent=self);return
        if not messagebox.askyesno(APP,tr('Install Footage Lab v{v0} from omne.space?\n\nUser settings and media are kept. The current application will be backed up.', v0=info.get('version')),parent=self):return
        self.update_install_running=True;self.update_status.set(tr('Downloading v{v0}…', v0=info.get('version')));self.refresh_update_panel()
        def work():
            try:
                updates=self.logger.state_dir/"updates";updates.mkdir(parents=True,exist_ok=True)
                suffix=Path(urllib.parse.urlparse(url).path).suffix or ".download"
                target=updates/("update_"+str(info.get("version"))+suffix);part=target.with_suffix(target.suffix+".partial")
                h=hashlib.sha256()
                with trusted_open(url,timeout=25) as response,part.open("wb") as out:
                    total=int(response.headers.get("Content-Length") or 0);done=0
                    if total>512*1024*1024:raise RuntimeError(tr('Update package exceeds download limit'))
                    while True:
                        chunk=response.read(512*1024)
                        if not chunk:break
                        done+=len(chunk)
                        if done>512*1024*1024:raise RuntimeError(tr('Update package exceeds download limit'))
                        out.write(chunk);h.update(chunk)
                        if total:self.ev.put(dict(update_download_progress=min(1,done/total)))
                if h.hexdigest()!=expected:
                    part.unlink(missing_ok=True);raise RuntimeError(tr('Update checksum mismatch; installation was not attempted'))
                os.replace(part,target)
                if kind in {"installer","exe","msi"}:
                    if os.name!="nt":raise RuntimeError(tr('This installer is not for the current platform'))
                    self.ev.put(dict(update_installer_ready=str(target),kind=kind));return
                if kind in {"pkg","dmg"}:
                    if sys.platform!="darwin":raise RuntimeError(tr('This installer is not for the current platform'))
                    self.ev.put(dict(update_installer_ready=str(target),kind=kind));return
                if kind!="zip-source" or getattr(sys,"frozen",False):raise RuntimeError(tr('This build requires a compatible installer asset'))
                backup=install_source_package(target,app_base_dir(),updates,str(info["version"]))
                self.ev.put(dict(update_installed=True,version=info["version"],backup=str(backup)))
            except Exception as e:self.ev.put(dict(update_install_error=str(e)))
        threading.Thread(target=work,daemon=True).start()

    def restart_app(self):
        try:
            if getattr(sys,"frozen",False):cmd=[sys.executable]
            else:cmd=[sys.executable,str(Path(__file__).resolve())]
            subprocess.Popen(cmd,cwd=str(Path.home()))
        finally:self.close(force=True)

    def browse_src(self):
        x=filedialog.askdirectory(initialdir=self.src.get() or str(Path.home()))
        if x:
            self.src.set(x); self.out.set(x+"_OMNE_FOOTAGE_LAB"); self.scan(); self.save_preferences(silent=True)
    def browse_out(self):
        x=filedialog.askdirectory(initialdir=self.out.get() or str(Path.home()))
        if x:
            self.out.set(x); self.refresh_summary(); self.save_preferences(silent=True)

    def scan(self):
        p=Path(self.src.get()).expanduser()
        if not p.is_dir():messagebox.showerror(APP,tr('Folder not found:\n{v0}', v0=p)); return
        output_root=Path(self.out.get()).expanduser().resolve()
        self.files=[x for x in sorted(p.rglob("*")) if x.is_file() and x.suffix.lower() in EXTS and not x.resolve().is_relative_to(output_root)]
        self.source_names={str(x.relative_to(p)):x for x in self.files}
        self.pscombo["values"]=list(self.source_names)
        total=sum(x.stat().st_size for x in self.files)
        self.scanstatus.set(tr('{v0} videos · {v1:.2f} GiB', v0=len(self.files), v1=total / 1024 ** 3))
        self.apply_folder_btn.configure(text=self.t("apply_folder_count","{label} ({count})").format(label=self.t("apply_folder","Apply Folder"),count=len(self.files)))
        self.logger.write(f"Scanned {p}: {len(self.files)} videos, {total} bytes")
        if self.files:
            wanted=self.pending_preview_source or self.previewsrc.get()
            chosen=wanted if wanted in self.source_names else next((n for n,x in self.source_names.items() if x.name==wanted),next(iter(self.source_names)))
            self.previewsrc.set(chosen); self.pending_preview_source=""; self.preview_source_info()
        self.refresh_summary(); self.save_preferences(silent=True)

    def selected_source(self):
        n=self.previewsrc.get(); return getattr(self,"source_names",{}).get(n) or next((x for x in self.files if x.name==n),None)

    def preview_source_info(self):
        p=self.selected_source()
        if not p:return
        try:
            i=self.preview_proc.probe(p)
            self.pstatus.set(tr('{v0}×{v1} · {v2:.2f} fps · {v3:.1f}s · {v4:.1f} MiB', v0=i['w'], v1=i['h'], v2=i['fps'], v3=i['dur'], v4=i['size'] / 1048576))
        except Exception as e:self.pstatus.set(str(e))

    def mode_changed(self):
        self.nb.select(0 if self.mode.get()=="lossless" else 1)
        self.refresh_summary()

    def use_preset(self):
        self.mode.set("glitch"); self.nb.select(1)
        d=self.presets.get(self.preset.get(),{})
        m={"resolution":self.res,"fps":self.fps,"crf":self.crf,"bitrate":self.bitrate,"x264":self.x264,
           "generation":self.generation,"scan":self.scanv,"interp":self.interp,"interp_fps":self.interpfps,
           "echo":self.echo,"decay":self.decay,"glow":self.glow,"chroma":self.chroma,"blur":self.blur,
           "warp":self.warp,"sat":self.sat,"hue":self.hue}
        for k,v in d.items():
            if k in m:m[k].set(v)
        self.refresh_summary(); self.save_preferences(silent=True)

    def preset_names(self):
        return list(PRESETS.keys())+sorted(self.custom_presets.keys(),key=str.casefold)

    def refresh_preset_values(self):
        if hasattr(self,"preset_combo"):
            self.preset_combo["values"]=[self.display_preset(x) for x in self.preset_names()]
        if self.preset.get() not in self.presets:
            self.preset.set("Manual")

    def read_custom_presets(self):
        try:
            if not self.custom_presets_path.exists():return {}
            data=json.loads(self.custom_presets_path.read_text(encoding="utf-8"))
            presets=data.get("presets",data)
            if not isinstance(presets,dict):return {}
            return {str(k):v for k,v in presets.items() if str(k) not in PRESETS and isinstance(v,dict)}
        except Exception as e:
            self.logger.write(f"Custom preset load failed: {e}")
            return {}

    def write_custom_presets(self):
        self.config_dir.mkdir(parents=True,exist_ok=True)
        temp=self.custom_presets_path.with_suffix(".json.tmp")
        payload={"version":1,"presets":self.custom_presets}
        temp.write_text(json.dumps(payload,indent=2,sort_keys=True)+"\n",encoding="utf-8")
        temp.replace(self.custom_presets_path)

    def custom_preset_payload(self):
        return dict(
            resolution=self.res.get(),fps=float(self.fps.get()),crf=int(self.crf.get()),bitrate=float(self.bitrate.get()),x264=self.x264.get(),
            generation=int(self.generation.get()),scan=float(self.scanv.get()),interp=bool(self.interp.get()),interp_fps=float(self.interpfps.get()),
            echo=int(self.echo.get()),decay=float(self.decay.get()),glow=float(self.glow.get()),chroma=float(self.chroma.get()),
            blur=float(self.blur.get()),warp=float(self.warp.get()),sat=float(self.sat.get()),hue=float(self.hue.get())
        )

    def save_custom_preset(self,name=None,confirm_overwrite=True):
        if name is None:
            name=simpledialog.askstring(self.t("preset_save_title","Save Custom Preset"),self.t("preset_name_prompt","Preset name:"),parent=self)
        if name is None:return False
        name=" ".join(str(name).strip().split())
        if not name:
            messagebox.showerror(APP,tr('Preset name cannot be empty.'),parent=self); return False
        if name in PRESETS:
            messagebox.showerror(APP,tr('Built-in preset names cannot be overwritten. Choose another name.'),parent=self); return False
        if name in self.custom_presets and confirm_overwrite:
            if not messagebox.askyesno(APP,tr('Overwrite custom preset "{v0}"?', v0=name),parent=self):return False
        self.custom_presets[name]=self.custom_preset_payload()
        self.presets={**PRESETS,**self.custom_presets}
        self.write_custom_presets(); self.refresh_preset_values()
        self.preset.set(name); self.mode.set("glitch"); self.nb.select(1)
        self.refresh_summary(); self.save_preferences(silent=True)
        self.qstatus.set(tr('Saved custom preset: {v0}', v0=name))
        self.logger.write(f"Saved custom preset: {name}")
        return True

    def preference_payload(self):
        return dict(
            version=1,source=self.src.get(),output=self.out.get(),max_mib=float(self.maxm.get()),mode=self.mode.get(),preset=self.preset.get(),
            resolution=self.res.get(),fps=float(self.fps.get()),crf=int(self.crf.get()),bitrate=float(self.bitrate.get()),x264=self.x264.get(),
            generation=int(self.generation.get()),scan=float(self.scanv.get()),interp=bool(self.interp.get()),interp_fps=float(self.interpfps.get()),
            echo=int(self.echo.get()),decay=float(self.decay.get()),glow=float(self.glow.get()),chroma=float(self.chroma.get()),blur=float(self.blur.get()),
            warp=float(self.warp.get()),sat=float(self.sat.get()),hue=float(self.hue.get()),preview_start=float(self.pstart.get()),preview_length=float(self.plen.get()),
            preview_source=self.previewsrc.get(),theme_name=self.theme_name.get(),show_startup=bool(self.show_startup.get()),check_updates=bool(self.check_updates_var.get()),enable_tooltips=bool(self.tooltips_enabled_var.get()),layout=self.saved_layout,collapsible=copy.deepcopy(self.collapsible_manual)
        )

    def save_preferences(self,silent=False):
        try:
            self.config_dir.mkdir(parents=True,exist_ok=True)
            temp=self.preferences_path.with_suffix(".json.tmp")
            temp.write_text(json.dumps(self.preference_payload(),indent=2,sort_keys=True)+"\n",encoding="utf-8")
            temp.replace(self.preferences_path)
            if not silent:self.qstatus.set(tr('Preferences saved'))
            return True
        except Exception as e:
            self.logger.write(f"Preferences save failed: {e}")
            if not silent:messagebox.showerror(APP,tr('Could not save preferences:\n{v0}', v0=e),parent=self)
            return False

    def load_preferences(self):
        data={}
        try:
            if self.preferences_path.exists():
                data=json.loads(self.preferences_path.read_text(encoding="utf-8"))
        except Exception as e:self.logger.write(f"Preferences load failed: {e}")
        values={**DEFAULT_UI,**(data if isinstance(data,dict) else {})}
        mapping={
            "source":self.src,"output":self.out,"max_mib":self.maxm,"mode":self.mode,"preset":self.preset,"resolution":self.res,"fps":self.fps,
            "crf":self.crf,"bitrate":self.bitrate,"x264":self.x264,"generation":self.generation,"scan":self.scanv,"interp":self.interp,
            "interp_fps":self.interpfps,"echo":self.echo,"decay":self.decay,"glow":self.glow,"chroma":self.chroma,"blur":self.blur,
            "warp":self.warp,"sat":self.sat,"hue":self.hue,"preview_start":self.pstart,"preview_length":self.plen,
            "show_startup":self.show_startup,"check_updates":self.check_updates_var,"enable_tooltips":self.tooltips_enabled_var,"theme_name":self.theme_name
        }
        for key,var in mapping.items():
            if key in values:
                try:var.set(values[key])
                except Exception:pass
        self.pending_preview_source=str(values.get("preview_source","") or "")
        self.previewsrc.set(self.pending_preview_source)
        if self.preset.get() not in self.presets:self.preset.set("Manual")
        self.saved_layout=values.get("layout",{}) if isinstance(values.get("layout",{}),dict) else {}
        self.collapsible_manual=values.get("collapsible",{}) if isinstance(values.get("collapsible",{}),dict) else {}
        self.auto_manage_collapsibles()
        geom=self.saved_layout.get("window_geometry") if isinstance(self.saved_layout,dict) else None
        if geom:
            try:self.geometry(str(geom))
            except Exception:pass
        self.mode_changed()
        self.set_tooltips_enabled(save=False)
        self.logger.write(f"Preferences loaded: source={self.src.get()} | output={self.out.get()} | tooltips={'on' if self.tooltips_enabled_var.get() else 'off'}")

    def reset_defaults(self,confirm=True):
        if confirm and not messagebox.askyesno(APP,tr('Reset folders and Inspector controls to application defaults?\n\nCustom presets and job history will be kept.'),parent=self):return False
        self.cancel_preview()
        mapping={
            "source":self.src,"output":self.out,"max_mib":self.maxm,"mode":self.mode,"preset":self.preset,"resolution":self.res,"fps":self.fps,
            "crf":self.crf,"bitrate":self.bitrate,"x264":self.x264,"generation":self.generation,"scan":self.scanv,"interp":self.interp,
            "interp_fps":self.interpfps,"echo":self.echo,"decay":self.decay,"glow":self.glow,"chroma":self.chroma,"blur":self.blur,
            "warp":self.warp,"sat":self.sat,"hue":self.hue,"preview_start":self.pstart,"preview_length":self.plen,
            "show_startup":self.show_startup,"check_updates":self.check_updates_var,"enable_tooltips":self.tooltips_enabled_var,"theme_name":self.theme_name
        }
        for key,var in mapping.items():var.set(DEFAULT_UI[key])
        self.set_tooltips_enabled(save=False)
        self.previewsrc.set(""); self.pending_preview_source=""
        self.saved_layout={}
        self.collapsible_manual={}
        self.auto_manage_collapsibles()
        self.after(80,self.restore_layout_sashes)
        self.files=[]; self.pscombo["values"]=[]; self.scanstatus.set(tr('Defaults restored · no folder scanned'))
        self.apply_folder_btn.configure(text=self.t("apply_folder","Apply Folder"))
        self.refresh_preset_values(); self.mode_changed(); self.refresh_summary(); self.save_preferences(silent=True)
        if Path(self.src.get()).expanduser().exists():self.after(50,self.scan)
        self.qstatus.set(tr('Defaults restored'))
        self.logger.write("Application defaults restored")
        return True

    def refresh_summary(self):
        try:
            if self.mode.get()=="lossless":
                self.summary.set(tr('LOSSLESS · original video/audio streams preserved · split only when required · ≤ {v0:g} MiB', v0=float(self.maxm.get())))
            else:
                extras=[]
                if self.interp.get():extras.append("interpolation")
                if self.warp.get()>0:extras.append("liquid warp")
                if self.echo.get()>1:extras.append(f"{self.echo.get()}-frame echo")
                tail=" · "+", ".join(extras) if extras else ""
                self.summary.set(tr('GLITCH · {v0} · {v1} @ {v2:g} fps · CRF {v3}{v4}', v0=self.preset.get(), v1=self.res.get(), v2=float(self.fps.get()), v3=self.crf.get(), v4=tail))
        except Exception:pass

    def settings(self):
        output=self.out.get().strip()
        if not output:
            output=self.src.get().rstrip("/")+"_OMNE_FOOTAGE_LAB"; self.out.set(output)
        return dict(output=output,max_mib=float(self.maxm.get()),resolution=self.res.get(),fps=float(self.fps.get()),
                    crf=int(self.crf.get()),bitrate=float(self.bitrate.get()),x264=self.x264.get(),generation=int(self.generation.get()),
                    scan=float(self.scanv.get()),interp=bool(self.interp.get()),interp_fps=float(self.interpfps.get()),
                    echo=int(self.echo.get()),decay=float(self.decay.get()),glow=float(self.glow.get()),chroma=float(self.chroma.get()),
                    blur=float(self.blur.get()),warp=float(self.warp.get()),sat=float(self.sat.get()),hue=float(self.hue.get()))

    def addjob(self,src,mode=None,preset=None,settings=None):
        jid=uuid.uuid4().hex[:10]; mode=mode or self.mode.get(); preset=preset or (self.preset.get() if mode=="glitch" else "Minimal Lossless")
        j=Job(jid,str(src),mode,preset,copy.deepcopy(settings or self.settings()))
        self.jobs[jid]=j; self.cancels[jid]=threading.Event()
        self.tree.insert("","end",iid=jid,values=(src.name,preset,"queued","0%","Queued"))
        self.jobq.put(jid); self.qstat(); self.logger.write(f"Queued {jid}: {src} | {mode} | {preset}")

    def cancel_preview(self):
        self.active_preview_token=None
        self.preview_cancel.set(); self.preview_proc.cancel(); self.stop(); self.preview_running=False
        if self.pprog.get()<1:self.pstatus.set(tr('Preview cancelled'))

    def enqueue_all(self):
        if not self.files:self.scan()
        if not self.files:return
        self.cancel_preview(); s=self.settings(); mode=self.mode.get(); preset=self.preset.get() if mode=="glitch" else "Minimal Lossless"
        for p in self.files:self.addjob(p,mode,preset,s)

    def enqueue_one(self):
        p=self.selected_source()
        if not p:return
        self.cancel_preview(); self.addjob(p)

    def persist_job(self,j):
        path=self.logger.state_dir/"jobs.jsonl"
        try:
            with path.open("a",encoding="utf-8") as h:h.write(json.dumps(j.__dict__,sort_keys=True)+"\n")
        except Exception as e:self.logger.write(f"Could not persist job {j.id}: {e}")

    def load_history(self):
        path=self.logger.state_dir/"jobs.jsonl"
        if not path.exists():return
        try:
            lines=path.read_text(encoding="utf-8",errors="replace").splitlines()[-30:]
            seen=set()
            for line in reversed(lines):
                d=json.loads(line); jid=d.get("id")
                if not jid or jid in seen:continue
                seen.add(jid); d["status"]="interrupted" if d.get("status") in {"queued","running"} else d.get("status","failed")
                j=Job(**{k:v for k,v in d.items() if k in Job.__dataclass_fields__})
                self.jobs[jid]=j; self.cancels[jid]=threading.Event()
                self.tree.insert("","end",iid=jid,values=(Path(j.source).name,self.display_preset(j.preset),self.display_state(j.status),f"{j.progress*100:.0f}%",j.message),tags=(j.status,))
        except Exception as e:self.logger.write(f"History load failed: {e}")
        self.qstat()

    def worker(self):
        while True:
            jid=self.jobq.get(); j=self.jobs[jid]; self.running=jid; j.status="running"; self.proc.set_task(jid)
            self.logger.write(f"JOB START {jid}: {j.source} | {j.mode} | {j.preset}")
            self.ev.put(dict(job_id=jid,status="running",message=tr('Starting')))
            try:
                outs=self.proc.lossless(j,self.cancels[jid]) if j.mode=="lossless" else self.proc.glitch(j,self.cancels[jid])
                j.outputs=[str(x) for x in outs]; j.status="completed"; j.progress=1; j.message=tr("{count} output(s) ready",count=len(outs))
                self.logger.write(f"JOB COMPLETE {jid}: {j.outputs}")
                self.ev.put(dict(job_id=jid,status="completed",progress=1,message=j.message))
            except Cancelled:
                j.status="cancelled"; j.message="Cancelled"; self.logger.write(f"JOB CANCELLED {jid}"); self.ev.put(dict(job_id=jid,status="cancelled",message=tr('Cancelled')))
            except Exception as e:
                j.status="failed"; j.message=str(e); self.logger.write(f"JOB FAILED {jid}: {e}"); self.ev.put(dict(job_id=jid,status="failed",message=str(e)))
            finally:
                self.persist_job(j); self.running=None; self.jobq.task_done(); self.ev.put(dict(queue=True))

    def poll(self):
        try:
            while True:
                e=self.ev.get_nowait()
                if "preview_token" in e and e["preview_token"]!=self.active_preview_token:continue
                if e.get("update_result"):
                    self.update_check_running=False
                    manifest=e.get("manifest") or {}
                    available=bool(e.get("available")); asset=e.get("asset")
                    self.update_info={"available":available,"version":str(manifest.get("version",VERSION)),"notes":str(manifest.get("notes") or ""),"asset":asset,"manifest":manifest}
                    if available and asset:
                        self.update_status.set(tr('Update v{v0} available', v0=self.update_info['version']))
                    elif available:
                        self.update_status.set(tr('v{v0} available · no {v1} package yet', v0=self.update_info['version'], v1=update_platform_key()))
                    else:
                        self.update_status.set(tr('v{v0} · up to date', v0=VERSION))
                    self.refresh_update_panel()
                    continue
                if "update_error" in e:
                    self.update_check_running=False
                    self.update_status.set(tr('Update check unavailable · app remains fully usable'))
                    self.logger.write("Update check failed: "+str(e.get("update_error")))
                    self.refresh_update_panel()
                    continue
                if "update_download_progress" in e:
                    self.update_status.set(tr('Downloading update… {v0:.0f}%', v0=float(e['update_download_progress']) * 100))
                    continue
                if "update_installer_ready" in e:
                    self.update_install_running=False
                    path=Path(e["update_installer_ready"])
                    self.update_status.set(tr('Update installer downloaded · launching…'))
                    self.refresh_update_panel()
                    try:open_path(path)
                    except Exception as ex:messagebox.showerror(APP,tr('Could not launch update installer:\n{v0}', v0=ex),parent=self)
                    else:messagebox.showinfo(APP,tr('The verified update installer has been launched. Close Footage Lab when the installer asks you to.'),parent=self)
                    continue
                if e.get("update_installed"):
                    self.update_install_running=False
                    self.update_status.set(tr('v{v0} installed · restart required', v0=e.get('version')))
                    self.refresh_update_panel()
                    if messagebox.askyesno(APP,tr('Update installed successfully. Restart Footage Lab now?'),parent=self):self.restart_app()
                    continue
                if "update_install_error" in e:
                    self.update_install_running=False
                    self.update_status.set(tr('Update installation failed · see Diagnostics'))
                    self.logger.write("Update install failed: "+str(e.get("update_install_error")))
                    self.refresh_update_panel()
                    messagebox.showerror(APP,tr('Update installation failed:\n{v0}', v0=str(e.get('update_install_error'))),parent=self)
                    continue
                if "preview_log" in e:self.preview_logs.append(e["preview_log"]); continue
                if "preview_progress" in e:self.pprog.set(e["preview_progress"]); self.pstatus.set(e.get("preview_message","")); continue
                if "preview_ready" in e:
                    self.preview_running=False; self.preview_frames=[Path(x) for x in e["frames"]]; self.pi=0; self.pprog.set(1); self.pstatus.set(e.get("message","Preview ready")); self.playing=True; self.nextframe(); continue
                if "preview_error" in e:
                    self.preview_running=False; self.pprog.set(0)
                    if e["preview_error"]=="Preview cancelled":
                        self.pstatus.set(tr('Preview cancelled')); self.image.configure(image="",text=tr('Preview cancelled'))
                    else:
                        self.pstatus.set(tr('Preview failed · open Diagnostics for the FFmpeg error')); self.image.configure(image="",text=tr('Preview failed\nUse Diagnostics… to copy the log')); self.logger.write("PREVIEW FAILED: "+e["preview_error"])
                    continue
                jid=e.get("job_id")
                if jid and jid in self.jobs:
                    j=self.jobs[jid]
                    if "log_file" in e and e["log_file"] not in j.logs:j.logs.append(e["log_file"])
                    if "status" in e:j.status=e["status"]
                    if "progress" in e:j.progress=e["progress"]
                    if "message" in e:j.message=e["message"]
                    msg=j.message
                    self.tree.item(jid,values=(Path(j.source).name,self.display_preset(j.preset),self.display_state(j.status),f"{j.progress*100:.0f}%",msg),tags=(j.status,))
                self.qstat()
        except queue.Empty:pass
        self.poll_after_id=self.after(120,self.poll)

    def qstat(self):
        c={x:sum(j.status==x for j in self.jobs.values()) for x in ("running","queued","completed","failed")}
        self.qstatus.set(tr('{v0} running · {v1} queued · {v2} done · {v3} failed', v0=c['running'], v1=c['queued'], v2=c['completed'], v3=c['failed']))

    def selected_job(self):
        x=self.tree.selection(); return self.jobs.get(x[0]) if x else None

    def retry(self):
        j=self.selected_job()
        if j:self.addjob(Path(j.source),j.mode,j.preset,j.settings)

    def repair(self):
        j=self.selected_job()
        if not j:return
        if j.status=="running":messagebox.showinfo(APP,tr('Cancel the running job before repairing it.')); return
        for x in j.outputs:
            try:Path(x).unlink(missing_ok=True)
            except Exception as e:self.logger.write(f"Repair could not remove {x}: {e}")
        self.addjob(Path(j.source),j.mode,j.preset,j.settings)

    def cancel(self):
        if self.running:self.cancels[self.running].set(); self.proc.cancel()

    def openout(self):
        p=Path(self.out.get() or (self.src.get().rstrip("/")+"_OMNE_FOOTAGE_LAB")); p.mkdir(parents=True,exist_ok=True); open_path(p)

    def preview_proxy_settings(self,src):
        s=self.settings(); info=self.preview_proc.probe(src)
        try:
            if s["resolution"]=="Source":w,h=info["w"],info["h"]
            else:w,h=map(int,s["resolution"].split("x"))
            if w>426:
                ratio=426/max(w,1); w=426; h=max(2,int(h*ratio)//2*2)
            s["resolution"]=f"{w}x{h}"
        except:s["resolution"]="426x240"
        s["fps"]=min(float(s["fps"]),15.0)
        if s["interp"]:s["interp_fps"]=min(float(s["interp_fps"]),8.0)
        s["x264"]="ultrafast"
        return s

    def preview(self):
        src=self.selected_source()
        if not src:return
        if self.preview_running:
            self.pstatus.set(tr('A preview is already rendering. Cancel it or wait before rendering again.')); return
        if self.running or any(j.status=="queued" for j in self.jobs.values()):
            self.pstatus.set(tr('Preview is paused while batch conversions are queued/running to preserve performance.')); return
        self.cancel_preview(); self.preview_cancel=threading.Event(); self.preview_running=True; self.preview_logs=[]; self.stop()
        if self.current_preview_dir:shutil.rmtree(self.current_preview_dir,ignore_errors=True)
        self.current_preview_dir=Path(tempfile.mkdtemp(dir=self.preview_tmp,prefix="render."))
        self.preview_frames=[]; self.image.cache.clear()
        self.image.configure(image="",text=tr('Rendering preview…')); self.pprog.set(0)
        s=self.preview_proxy_settings(src); j=Job("preview_"+uuid.uuid4().hex[:6],str(src),"glitch",self.preset.get(),s)
        start=max(0,float(self.pstart.get())); length=max(2,min(12,float(self.plen.get())))
        token=uuid.uuid4().hex; self.active_preview_token=token
        cancel_event=self.preview_cancel; preview_dir=self.current_preview_dir
        proc=Processor(lambda **kw:self.ev.put(dict(kw,preview_token=token)),self.logger,"preview")
        self.preview_proc=proc; proc.set_task(j.id)
        proxy_note=tr("Proxy {resolution} @ {fps:g} fps",resolution=s["resolution"],fps=s["fps"])
        self.pstatus.set(tr('{v0} · rendering…', v0=proxy_note))
        def run():
            try:
                mp4,frames=proc.glitch(j,cancel_event,preview=True,start=start,length=length,preview_root=preview_dir)
                fs=sorted(frames.glob("*.png"))
                if not fs:raise RuntimeError(tr('Preview render completed but no display frames were produced'))
                self.ev.put(dict(preview_ready=True,preview_token=token,frames=[str(x) for x in fs],message=tr('{v0} · ready', v0=proxy_note)))
            except Cancelled:self.ev.put(dict(preview_error="Preview cancelled",preview_token=token))
            except Exception as e:self.ev.put(dict(preview_error=str(e),preview_token=token))
        threading.Thread(target=run,daemon=True).start()

    def nextframe(self):
        if not self.playing or not self.preview_frames:return
        try:
            self.image.show_frame(self.preview_frames[self.pi])
            self.pi=(self.pi+1)%len(self.preview_frames); self.after_id=self.after(125,self.nextframe)
        except Exception as e:self.pstatus.set(tr('Preview display error: {v0}', v0=str(e))); self.playing=False
    def toggle(self):
        if not self.preview_frames:return
        self.playing=not self.playing
        if self.playing:self.nextframe()
        else:self.stop(False)
    def stop(self,setfalse=True):
        if setfalse:self.playing=False
        if self.after_id:
            try:self.after_cancel(self.after_id)
            except:pass
            self.after_id=None

    def diagnostics_text(self):
        try:settings=json.dumps(self.settings(),indent=2,sort_keys=True)
        except Exception as e:settings=f"<settings error: {e}>"
        try:ff=subprocess.run([FFMPEG_BIN or "ffmpeg","-version"],capture_output=True,text=True,timeout=5).stdout.splitlines()[0]
        except Exception as e:ff=f"ffmpeg version unavailable: {e}"
        lines=[f"{APP} {VERSION} DIAGNOSTICS",f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}",f"Platform: {platform.platform()}",f"Platform key: {update_platform_key()}",f"Python: {platform.python_version()}",f"UI profile schema: {self.ui_profile.get('schema')}",f"Preview scaler: {('Pillow ' + str(getattr(PIL, '__version__', 'unknown')) + ' · ' + _PIL_RESAMPLE_API) if Image else 'Tk fallback'}","Processing engine: CPU / FFmpeg (no discrete GPU required; GPU acceleration is not used by default)",ff,
               f"FFmpeg path: {FFMPEG_BIN}",f"FFprobe path: {FFPROBE_BIN}",f"Website: {WEBSITE_URL}",f"Support: {SUPPORT_URL}",f"Update manifest: {UPDATE_MANIFEST_URL}",f"Update status: {self.update_status.get()}",
               f"Source: {self.src.get()}",f"Output: {self.out.get()}",f"Scanned videos: {len(self.files)}",f"Current operation: {self.mode.get()}",f"Current preset: {self.preset.get()}",
               f"Preferences: {self.preferences_path}",f"Packaged UI profile: {app_base_dir()/UI_PROFILE_FILENAME}",f"Custom presets: {self.custom_presets_path}",f"Saved custom preset names: {', '.join(sorted(self.custom_presets)) or '<none>'}",
               "","CURRENT SETTINGS",settings,"","JOBS"]
        for j in self.jobs.values():
            lines.append(f"- {j.id} | {j.status} | {Path(j.source).name} | {j.preset} | {j.progress*100:.0f}% | {j.message}")
            for log in j.logs[-3:]:lines.append(f"    log: {log}")
        lines += ["","PREVIEW",f"Status: {self.pstatus.get()}"]
        for log in self.preview_logs[-4:]:lines.append(f"preview log: {log}")
        selected=self.selected_job()
        if selected and selected.logs:
            lines += ["","SELECTED JOB LAST FFMPEG LOG",self.logger.tail(selected.logs[-1],80)]
        elif self.preview_logs:
            lines += ["","LAST PREVIEW FFMPEG LOG",self.logger.tail(self.preview_logs[-1],80)]
        lines += ["","SESSION LOG (last 100 lines)",self.logger.tail(lines=100),"",f"Log folder: {self.logger.log_dir}"]
        return "\n".join(lines)

    def copy_text(self,text):
        self.clipboard_clear(); self.clipboard_append(text); self.update_idletasks(); self.qstatus.set(tr('Copied diagnostics to clipboard'))

    def show_diagnostics(self):
        win=tk.Toplevel(self); win.title(self.t("diagnostics_title","{app} Diagnostics").format(app=APP)); win.geometry("920x650")
        win.minsize(400,280)
        textbody=ttk.Frame(win,padding=6); textbody.pack(fill="both",expand=True)
        textbody.rowconfigure(0,weight=1); textbody.columnconfigure(0,weight=1)
        text=self.add_tip(tk.Text(textbody,wrap="word",font=(self.ui_chrome["mono_font"],self.ui_chrome["mono_size"]),bg=self.ui_chrome["field_bg"],fg=self.ui_chrome["field_fg"]),"diagnostics_text")
        text.grid(row=0,column=0,sticky="nsew"); text.insert("1.0",self.diagnostics_text())
        vs=self.add_tip(AutoScrollbar(textbody,orient="vertical",command=text.yview),"scroll_vertical"); vs.grid(row=0,column=1,sticky="ns"); text.configure(yscrollcommand=vs.set)
        buttons=self.scroll_section(win,"diagnostic_actions",height=58); buttons.pack(fill="x")
        for key,label,command in [("copy_all","Copy All",lambda:self.copy_text(text.get("1.0","end-1c"))),
                                  ("refresh","Refresh",lambda:(text.delete("1.0","end"),text.insert("1.0",self.diagnostics_text()))),
                                  ("open_logs_folder","Open Logs Folder",self.open_logs)]:
            self.add_tip(ttk.Button(buttons.body,text=self.t(key,label),command=command),key).pack(side="left",padx=4)
        self._scroll_register(win)

    def copy_job_log(self):
        j=self.selected_job()
        if j and j.logs:self.copy_text(self.logger.tail(j.logs[-1],160))
        elif self.preview_logs:self.copy_text(self.logger.tail(self.preview_logs[-1],160))
        else:self.copy_text(self.diagnostics_text())

    def open_logs(self):
        open_path(self.logger.log_dir)

    def close(self,force=False):
        if self.running and not force and not messagebox.askyesno(APP,tr('Cancel running conversion and quit?')):return
        try:self.save_layout_sashes()
        except Exception:pass
        self.save_preferences(silent=True)
        self.cancel(); self.cancel_preview(); self.stop()
        for attr in ("poll_after_id","layout_after_id","startup_after_id","update_after_id","_layout_clamp_after"):
            aid=getattr(self,attr,None)
            if aid:
                try:self.after_cancel(aid)
                except Exception:pass
                setattr(self,attr,None)
        shutil.rmtree(self.preview_tmp,ignore_errors=True); self.logger.write("Session closed; preferences saved"); self.destroy()

def main():
    missing=[name for name,value in (("ffmpeg",FFMPEG_BIN),("ffprobe",FFPROBE_BIN)) if not value]
    if missing:
        r=tk.Tk(); r.withdraw(); messagebox.showerror(APP,tr('Missing: {v0}\n\nLinux: install FFmpeg with your package manager.\nWindows: install FFmpeg or use the packaged release that bundles it.', v0=', '.join(missing))); return
    App().mainloop()

if __name__=="__main__": main()
