"""
PDF Tool Pro – Divisione, Rotazione, Unione (Avvisi+PagoPA)
Requisiti: pip install PyPDF2 tkinterdnd2 pdfplumber
"""

import os
import re
import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext, filedialog
from tkinterdnd2 import DND_FILES, TkinterDnD
import PyPDF2
import pdfplumber
import shutil

class PDFToolApp:
    def __init__(self, root):
        self.root = root
        self.root.title("PDF Tool Pro – Divisione e Rotazione")
        self.root.geometry("900x800")
        self.root.minsize(900, 800)

        self.colors = {
            'primary': '#1a73e8', 'primary_dark': '#1557b0', 'secondary': '#34a853',
            'warning': '#fbbc04', 'danger': '#ea4335', 'dark': '#202124',
            'light_bg': '#f8f9fa', 'card_bg': '#ffffff', 'text_dark': '#202124',
            'text_light': '#5f6368', 'border': '#dadce0'
        }
        # --- variabili di istanza ---
        self.menu_open = False
        self.btn_list   = []            # <- mancava
        self.simple_merge_list = []
        self.custom_search_string = None
        self.stop_analysis_flag = False

        # --- nuove variabili per Rinomina ---
        self.rename_source_paths = []
        self.current_rename_base = tk.StringVar(value="Documento")

        self.pdf_path = None
        self.avvisi = []
        self.current_section = "split"
        self.merge_source_a = None
        self.merge_source_b = None
        self.setup_ui()
        self.show_section("split")
        self.update_search_pattern_label()
        self.rename_source_paths = []   # lista percorsi PDF
        self.split250_source_folder = None
        self.split250_pdf_list = []

    # ---------- GUI ----------
    def setup_ui(self):
        self.root.configure(bg=self.colors['light_bg'])

        # ---------- BARRA SUPERIORE (solo icona ≡ + titolo) ----------
        top = tk.Frame(self.root, bg=self.colors['dark'], height=55)
        top.pack(fill="x", side="top")
        top.pack_propagate(False)

        # Icona hamburger
        self.hamburger = tk.Label(top, text="≡", font=("Segoe UI", 22, "bold"),
                                  bg=self.colors['dark'], fg="white", cursor="hand2")
        self.hamburger.pack(side="left", padx=15)
        self.hamburger.bind("<Button-1>", lambda e: self.toggle_side_menu())

        # Titolo
        tk.Label(top, text="📄 PDF Tool Pro", font=("Segoe UI", 16, "bold"),
                 bg=self.colors['dark'], fg="white").pack(side="left", padx=10)

        # ---------- MENÙ LATERALE (nascosto all'inizio) ----------
        self.side_menu = tk.Frame(self.root, bg=self.colors['dark'], width=0)
        self.side_menu.pack(side="left", fill="y")
        self.side_menu.pack_propagate(False)

        # voci menù
        menu_items = [
            ("✂️  Divisione",  "split",   self.colors['primary']),
            ("🔄  Rotazione",  "rotate",  self.colors['warning']),
            ("🔗  Unisci",     "merge",   '#9c27b0'),
            ("✏️  Rinomina",   "rename",  '#ff9800'),
            ("📦 Split-250",   "split250",'#00bcd4')
        ]
        for txt, sec, col in menu_items:
            btn = tk.Button(self.side_menu, text=txt,
                            command=lambda s=sec: self.show_section(s),
                            bg=col, fg="white", font=("Segoe UI", 11, "bold"),
                            anchor="w", padx=20, pady=10, relief="flat", bd=0,
                            cursor="hand2", width=18)
            btn.pack(fill="x", padx=2, pady=2)
            self.btn_list.append(btn)

        # ---------- CONTENITORE PRINCIPALE ----------
        self.container = tk.Frame(self.root, bg=self.colors['light_bg'])
        self.container.pack(side="right", fill="both", expand=True, padx=20, pady=20)

        # inizializza frame sezioni
        self.setup_split_section()
        self.setup_rotate_section()
        self.setup_merge_section()
        self.setup_rename_section()
        self.setup_split250_section()
        self.show_section("split")

    # ---------- SPLIT ----------
    def setup_split_section(self):
        self.split_frame = tk.Frame(self.container, bg=self.colors['light_bg'])

        method_frame = tk.Frame(self.split_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        method_frame.pack(fill="x", pady=(0, 15))
        tk.Frame(method_frame, bg=self.colors['primary'], height=10).pack(fill="x")
        method_content = tk.Frame(method_frame, bg=self.colors['card_bg'])
        method_content.pack(fill="x", padx=20, pady=15)

        tk.Label(method_content, text="⚙️ Metodo di divisione", font=("Segoe UI", 12, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 10))
        self.split_method = tk.StringVar(value="cf")

        rb_cf_frame = tk.Frame(method_content, bg=self.colors['card_bg'])
        rb_cf_frame.pack(anchor="w", pady=6, fill="x")
        tk.Radiobutton(rb_cf_frame, text="🔍 Divisione per marcatore:", variable=self.split_method, value="cf", font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text_dark'], command=self.on_method_change).pack(side="left")
        self.search_pattern_label = tk.Label(rb_cf_frame, text="(Non configurato)", font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg=self.colors['danger'])
        self.search_pattern_label.pack(side="left", padx=4)
        self.custom_string_btn = tk.Button(rb_cf_frame, text="⚙️ Configura", command=self.configure_search_string, font=("Segoe UI", 9), bg=self.colors['primary'], fg="white", padx=12, pady=4, relief="flat", cursor="hand2", border=0, state="normal")
        self.custom_string_btn.pack(side="left", padx=8)

        rb_pages_frame = tk.Frame(method_content, bg=self.colors['card_bg'])
        rb_pages_frame.pack(anchor="w", pady=6, fill="x")
        tk.Radiobutton(rb_pages_frame, text="📄 Divisione ogni", variable=self.split_method, value="pages", font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text_dark'], command=self.on_method_change).pack(side="left")
        self.pages_entry = tk.Entry(rb_pages_frame, width=6, font=("Segoe UI", 10), relief="solid", bd=1)
        self.pages_entry.pack(side="left", padx=8)
        self.pages_entry.insert(0, "1")
        self.pages_entry.config(state="disabled")
        tk.Label(rb_pages_frame, text="pagine per file", font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(side="left")

        drop_card = tk.Frame(self.split_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        drop_card.pack(fill="x", pady=(0, 15))
        tk.Frame(drop_card, bg=self.colors['primary'], height=10).pack(fill="x")
        drop_content = tk.Frame(drop_card, bg=self.colors['card_bg'])
        drop_content.pack(fill="both", expand=True, padx=25, pady=20)
        self.drop_label_split = tk.Label(drop_content, text="📄 Trascina qui il PDF o clicca", font=("Segoe UI", 12), bg="#f0f7ff", fg=self.colors['text_light'], relief="solid", bd=2, height=3, cursor="hand2")
        self.drop_label_split.pack(fill="both", expand=True)
        self.drop_label_split.drop_target_register(DND_FILES)
        self.drop_label_split.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, "split"))
        self.drop_label_split.bind('<Button-1>', lambda e: self.select_file("split"))
        self.file_label_split = tk.Label(drop_content, text="Nessun file selezionato", fg=self.colors['text_light'], bg=self.colors['card_bg'], font=("Segoe UI", 10))
        self.file_label_split.pack(pady=(10, 0))

        control_frame = tk.Frame(self.split_frame, bg=self.colors['light_bg'])
        control_frame.pack(pady=10)
        self.analyze_btn = tk.Button(control_frame, text="🔍  Analizza PDF", command=self.start_analysis, state="disabled", font=("Segoe UI", 11, "bold"), bg=self.colors['secondary'], fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.analyze_btn.pack(side="left", padx=5)
        self.stop_btn = tk.Button(control_frame, text="🛑 Blocca Scansione", command=self.stop_analysis, state="disabled", font=("Segoe UI", 11, "bold"), bg=self.colors['danger'], fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.stop_btn.pack(side="left", padx=5)

        results_card = tk.Frame(self.split_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        results_card.pack(fill="both", expand=True, pady=(0, 10))
        tk.Frame(results_card, bg=self.colors['primary'], height=8).pack(fill="x")
        results_content = tk.Frame(results_card, bg=self.colors['card_bg'])
        results_content.pack(fill="both", expand=True, padx=20, pady=15)
        tk.Label(results_content, text="📊 Risultati & Log Dettagliato", font=("Segoe UI", 12, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 8))
        self.results_text = scrolledtext.ScrolledText(results_content, height=6, font=("Consolas", 9), state="disabled", relief="flat", bg="#f8f9fa", wrap="word")
        self.results_text.pack(fill="both", expand=True)

        button_frame = tk.Frame(self.split_frame, bg=self.colors['light_bg'])
        button_frame.pack(pady=10)
        self.split_btn = tk.Button(button_frame, text="✂️  Dividi PDF", command=self.split_pdf, state="disabled", font=("Segoe UI", 11, "bold"), bg=self.colors['primary'], fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.split_btn.pack(side="left", padx=6)
        self.reset_btn_split = tk.Button(button_frame, text="🔄  Reset", command=lambda: self.reset("split"), font=("Segoe UI", 11, "bold"), bg=self.colors['text_light'], fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.reset_btn_split.pack(side="left", padx=6)

    # ---------- ROTATE ----------
    def setup_rotate_section(self):
        self.rotate_frame = tk.Frame(self.container, bg=self.colors['light_bg'])
        info_card = tk.Frame(self.rotate_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        info_card.pack(fill="x", pady=(0, 15))
        tk.Frame(info_card, bg=self.colors['warning'], height=10).pack(fill="x")
        info_content = tk.Frame(info_card, bg=self.colors['card_bg'])
        info_content.pack(fill="x", padx=20, pady=15)
        tk.Label(info_content, text="ℹ️  Informazioni", font=("Segoe UI", 12, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 8))
        tk.Label(info_content, text="Questa funzione ruota automaticamente di 270° tutte le pagine\norizzontali per renderle verticali e facilmente leggibili.", font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text_light'], justify="left").pack(anchor="w")

        drop_card = tk.Frame(self.rotate_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        drop_card.pack(fill="x", pady=(0, 15))
        tk.Frame(drop_card, bg=self.colors['warning'], height=10).pack(fill="x")
        drop_content = tk.Frame(drop_card, bg=self.colors['card_bg'])
        drop_content.pack(fill="both", expand=True, padx=25, pady=20)
        self.drop_label_rotate = tk.Label(drop_content, text="📄 Trascina qui il PDF o clicca", font=("Segoe UI", 12), bg="#fffbf0", fg=self.colors['text_light'], relief="solid", bd=2, height=3, cursor="hand2")
        self.drop_label_rotate.pack(fill="both", expand=True)
        self.drop_label_rotate.drop_target_register(DND_FILES)
        self.drop_label_rotate.dnd_bind('<<Drop>>', lambda e: self.on_drop(e, "rotate"))
        self.drop_label_rotate.bind('<Button-1>', lambda e: self.select_file("rotate"))
        self.file_label_rotate = tk.Label(drop_content, text="Nessun file selezionato", fg=self.colors['text_light'], bg=self.colors['card_bg'], font=("Segoe UI", 10))
        self.file_label_rotate.pack(pady=(10, 0))

        log_card = tk.Frame(self.rotate_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        log_card.pack(fill="both", expand=True, pady=(0, 15))
        tk.Frame(log_card, bg=self.colors['warning'], height=10).pack(fill="x")
        log_content = tk.Frame(log_card, bg=self.colors['card_bg'])
        log_content.pack(fill="both", expand=True, padx=25, pady=20)
        tk.Label(log_content, text="📋 Log operazioni", font=("Segoe UI", 13, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 10))
        self.log_text = scrolledtext.ScrolledText(log_content, height=6, font=("Consolas", 9), state="disabled", relief="flat", bg="#f8f9fa", wrap="word")
        self.log_text.pack(fill="both", expand=True)

        button_frame = tk.Frame(self.rotate_frame, bg=self.colors['light_bg'])
        button_frame.pack(pady=10)
        self.rotate_btn = tk.Button(button_frame, text="🔄  Ruota Pagine", command=self.rotate_pdf, state="disabled", font=("Segoe UI", 11, "bold"), bg=self.colors['warning'], fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.rotate_btn.pack(side="left", padx=6)
        self.reset_btn_rotate = tk.Button(button_frame, text="🔄  Reset", command=lambda: self.reset("rotate"), font=("Segoe UI", 11, "bold"), bg=self.colors['text_light'], fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.reset_btn_rotate.pack(side="left", padx=6)

    # ---------- MERGE ----------
    def setup_merge_section(self):
        self.merge_frame = tk.Frame(self.container, bg=self.colors['light_bg'])

        logic_frame = tk.Frame(self.merge_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        logic_frame.pack(fill="x", pady=(0, 10))
        tk.Frame(logic_frame, bg='#9c27b0', height=8).pack(fill="x")
        logic_content = tk.Frame(logic_frame, bg=self.colors['card_bg'])
        logic_content.pack(fill="x", padx=15, pady=10)
        tk.Label(logic_content, text="⚙️ Logica", font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 6))
        self.merge_logic = tk.StringVar(value="progressive")
        tk.Radiobutton(logic_content, text="🔢 Progressivo (Avvisi+PagoPA)", variable=self.merge_logic, value="progressive", font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text_dark'], command=self.toggle_merge_interface).pack(anchor="w", pady=2)
        tk.Radiobutton(logic_content, text="📎 Semplice (ordine manuale)", variable=self.merge_logic, value="simple", font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text_dark'], command=self.toggle_merge_interface).pack(anchor="w", pady=2)

        self.merge_interface_container = tk.Frame(self.merge_frame, bg=self.colors['light_bg'])
        self.merge_interface_container.pack(fill="both", expand=True, pady=(0, 8))

        # PROGRESSIVO
        self.progressive_merge_frame = tk.Frame(self.merge_interface_container, bg=self.colors['light_bg'])
        main_frame = tk.Frame(self.progressive_merge_frame, bg=self.colors['light_bg'])
        main_frame.pack(fill="both", expand=True, pady=(0, 8))
        for side in ("a", "b"):
            col = tk.Frame(main_frame, bg=self.colors['light_bg'])
            col.pack(side="left" if side == "a" else "right", fill="both", expand=True, padx=(0, 4) if side == "a" else (4, 0))
            card = tk.Frame(col, bg=self.colors['card_bg'], relief="flat", bd=0)
            card.pack(fill="both", expand=True)
            tk.Frame(card, bg='#9c27b0', height=8).pack(fill="x")
            content = tk.Frame(card, bg=self.colors['card_bg'])
            content.pack(fill="both", expand=True, padx=12, pady=10)
            tk.Label(content, text=f"📂 {'A - Sinistra' if side == 'a' else 'B - Destra'}", font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 6))
            var = tk.StringVar(value="folder")
            setattr(self, f"merge_type_{side}", var)
            rb_frame = tk.Frame(content, bg=self.colors['card_bg'])
            rb_frame.pack(anchor="w", fill="x")
            tk.Radiobutton(rb_frame, text="📁 Cartella", variable=var, value="folder", font=("Segoe UI", 8), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(side="left", padx=(0, 8))
            drop = tk.Label(content, text="Trascina cartella", font=("Segoe UI", 9), bg="#f3e5f5", fg=self.colors['text_light'], relief="solid", bd=2, height=3, cursor="hand2", wraplength=180)
            drop.pack(fill="both", expand=True, pady=(6, 0))
            drop.drop_target_register(DND_FILES)
            drop.dnd_bind('<<Drop>>', lambda e, s=side: self.on_drop_merge(e, s))
            drop.bind('<Button-1>', lambda e, s=side: self.select_file(s))
            lbl = tk.Label(content, text="", fg=self.colors['text_light'], bg=self.colors['card_bg'], font=("Segoe UI", 8), wraplength=180)
            lbl.pack(pady=(4, 0))
            setattr(self, f"drop_label_merge_{side}", drop)
            setattr(self, f"file_label_merge_{side}", lbl)

        # SEMPLICE
        self.simple_merge_frame = tk.Frame(self.merge_interface_container, bg=self.colors['light_bg'])
        simple_card = tk.Frame(self.simple_merge_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        simple_card.pack(fill="both", expand=True)
        tk.Frame(simple_card, bg='#9c27b0', height=8).pack(fill="x")
        simple_content = tk.Frame(simple_card, bg=self.colors['card_bg'])
        simple_content.pack(fill="both", expand=True, padx=15, pady=10)
        tk.Label(simple_content, text="📋 Lista File da Unire (ordine personalizzabile)", font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 8))
        list_frame = tk.Frame(simple_content, bg=self.colors['card_bg'])
        list_frame.pack(fill="both", expand=True, pady=(0, 8))
        scrollbar = tk.Scrollbar(list_frame)
        scrollbar.pack(side="right", fill="y")
        self.simple_merge_listbox = tk.Listbox(list_frame, height=8, font=("Segoe UI", 9), relief="solid", bd=1, yscrollcommand=scrollbar.set)
        self.simple_merge_listbox.pack(side="left", fill="both", expand=True)
        scrollbar.config(command=self.simple_merge_listbox.yview)
        self.simple_merge_listbox.drop_target_register(DND_FILES)
        self.simple_merge_listbox.dnd_bind('<<Drop>>', self.on_drop_merge_simple)
        control_frame = tk.Frame(simple_content, bg=self.colors['card_bg'])
        control_frame.pack(fill="x", pady=(0, 4))
        tk.Button(control_frame, text="➕ Aggiungi File", command=lambda: self.select_file_simple("file"), font=("Segoe UI", 9), bg=self.colors['secondary'], fg="white", padx=12, pady=6, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(control_frame, text="📁 Aggiungi Cartella", command=lambda: self.select_file_simple("folder"), font=("Segoe UI", 9), bg=self.colors['secondary'], fg="white", padx=12, pady=6, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(control_frame, text="❌ Rimuovi", command=self.remove_simple_merge_item, font=("Segoe UI", 9), bg=self.colors['danger'], fg="white", padx=12, pady=6, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(control_frame, text="⬆️ Su", command=lambda: self.move_simple_merge_item(-1), font=("Segoe UI", 9), bg=self.colors['primary'], fg="white", padx=12, pady=6, relief="flat", cursor="hand2").pack(side="left", padx=2)
        tk.Button(control_frame, text="⬇️ Giù", command=lambda: self.move_simple_merge_item(1), font=("Segoe UI", 9), bg=self.colors['primary'], fg="white", padx=12, pady=6, relief="flat", cursor="hand2").pack(side="left", padx=2)

        log_card = tk.Frame(self.merge_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        log_card.pack(fill="both", expand=True, pady=(0, 8))
        tk.Frame(log_card, bg='#9c27b0', height=8).pack(fill="x")
        log_content = tk.Frame(log_card, bg=self.colors['card_bg'])
        log_content.pack(fill="both", expand=True, padx=15, pady=8)
        tk.Label(log_content, text="📋 Anteprima", font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 4))
        # Label stato anteprima (progressiva)
        self.preview_status_lbl = tk.Label(log_content, text="", font=("Segoe UI", 9, "bold"), bg=self.colors['card_bg'])
        self.preview_status_lbl.pack(anchor="w", pady=(2, 0))
        self.merge_log_text = scrolledtext.ScrolledText(log_content, height=3, font=("Consolas", 8), state="disabled", relief="flat", bg="#f8f9fa", wrap="word")
        self.merge_log_text.pack(fill="both", expand=True)

        button_frame = tk.Frame(self.merge_frame, bg=self.colors['light_bg'])
        button_frame.pack(pady=8)
        self.merge_btn = tk.Button(button_frame, text="🔗  Unisci PDF", command=self.merge_pdfs, state="disabled", font=("Segoe UI", 11, "bold"), bg='#9c27b0', fg="white", padx=22, pady=10, relief="flat", cursor="hand2", border=0)
        self.merge_btn.pack(side="left", padx=5)
        self.reset_btn_merge = tk.Button(button_frame, text="🔄  Reset", command=lambda: self.reset("merge"), font=("Segoe UI", 11, "bold"), bg=self.colors['text_light'], fg="white", padx=22, pady=10, relief="flat", cursor="hand2", border=0)
        self.reset_btn_merge.pack(side="left", padx=5)

        self.toggle_merge_interface()
        self.update_merge_log()

    # ---------- MERGE LOGIC ----------
    def toggle_merge_interface(self):
        selected = self.merge_logic.get()
        self.progressive_merge_frame.pack_forget()
        self.simple_merge_frame.pack_forget()
        if selected == "progressive":
            self.progressive_merge_frame.pack(fill="both", expand=True)
        else:
            self.simple_merge_frame.pack(fill="both", expand=True)
        self.update_merge_log()

    def get_merge_files(self, source_path):
        if not source_path: return []
        if os.path.isfile(source_path) and source_path.lower().endswith('.pdf'):
            return [source_path]
        if os.path.isdir(source_path):
            files = [os.path.join(source_path, f) for f in os.listdir(source_path)]
            pdf_files = [f for f in files if os.path.isfile(f) and f.lower().endswith('.pdf')]
            return sorted(pdf_files)
        return []

    def update_merge_log(self):
        """Anteprima in TEMPO REALE per logica PROGRESSIVA + SEMPLICE"""
        if not hasattr(self, 'merge_log_text'):
            return

        self.merge_log_text.config(state="normal")
        self.merge_log_text.delete(1.0, tk.END)

        current = self.merge_logic.get()

        # ---------- PROGRESSIVA ----------
        if current == "progressive":
            a_paths = self.get_merge_files(self.merge_source_a)
            b_paths = self.get_merge_files(self.merge_source_b)

            # Costruisci dizionari progressivo -> path
            a_dict, b_dict = {}, {}
            for p in a_paths:
                prog = self.extract_progressive_from_filename(os.path.basename(p))
                if prog:
                    a_dict[prog] = p
                else:
                    self.merge_log_text.insert(tk.END, f"⚠️ A: nessun progressivo in {os.path.basename(p)}\n")
            for p in b_paths:
                prog = self.extract_progressive_from_filename(os.path.basename(p))
                if prog:
                    b_dict[prog] = p
                else:
                    self.merge_log_text.insert(tk.END, f"⚠️ B: nessun progressivo in {os.path.basename(p)}\n")

            # Tutti i progressivi
            all_progs = sorted(set(a_dict) | set(b_dict))
            common    = sorted(set(a_dict) & set(b_dict))
            only_a    = sorted(set(a_dict) - set(b_dict))
            only_b    = sorted(set(b_dict) - set(a_dict))

            # Preview
            if not all_progs:
                self.merge_log_text.insert(tk.END, "Trascina le cartelle A e B per vedere l'anteprima.\n")
                self.merge_btn.config(state="disabled")
                self.merge_log_text.config(state="disabled")
                return

            self.merge_log_text.insert(tk.END, f"📊 Anteprima Unione Progressiva\n")
            self.merge_log_text.insert(tk.END, f"A: {len(a_paths)} file  |  B: {len(b_paths)} file\n")
            self.merge_log_text.insert(tk.END, f"Coppie valide trovate: {len(common)}\n\n")
            # Colora la label di stato
            if len(common) == 0:
                self.preview_status_lbl.config(text="❌ Nessuna coppia valida", fg=self.colors['danger'])
            elif only_a or only_b:
                self.preview_status_lbl.config(text=f"⚠️  Ci sono progressivi mancanti", fg=self.colors['warning'])
            else:
                self.preview_status_lbl.config(text=f"✅ Tutte le coppie sono complete", fg=self.colors['secondary'])

            # Elenco coppie
            for prog in common:
                a_name = os.path.basename(a_dict[prog])
                b_name = os.path.basename(b_dict[prog])
                self.merge_log_text.insert(tk.END, f"✅ {prog:<4} ➜  A: {a_name}\n")
                self.merge_log_text.insert(tk.END, f"     {'':4}  ➜  B: {b_name}\n\n")

            # Errori
            if only_a:
                self.merge_log_text.insert(tk.END, f"⚠️  Mancano in B: {', '.join(only_a)}\n")
            if only_b:
                self.merge_log_text.insert(tk.END, f"⚠️  Mancano in A: {', '.join(only_b)}\n")

            # Stato pulsante
            if len(common) == 0:
                self.merge_btn.config(state="disabled", bg=self.colors['text_light'])
                self.merge_log_text.insert(tk.END, "\n❌ Nessuna coppia valida – impossibile proseguire.\n")
            else:
                self.merge_btn.config(state="normal", bg='#9c27b0')

        # ---------- SEMPLICE ----------
        else:
            if not self.simple_merge_list:
                self.merge_btn.config(state="disabled")
                self.merge_log_text.insert(tk.END, "Logica SEMPLICE (ordine manuale)\n\nClicca 'Aggiungi' o trascina per creare la lista.")
            else:
                self.merge_btn.config(state="normal")
                self.merge_log_text.insert(tk.END, f"Logica SEMPLICE ({len(self.simple_merge_list)} file in lista)\n\n")
                for _, _, name in self.simple_merge_list:
                    self.merge_log_text.insert(tk.END, f"📄 {name}\n")

        self.merge_log_text.config(state="disabled")

    def extract_progressive_from_filename(self, filename):
        """
        Estrae il progressivo "puro" (senza zeri iniziali) dal nome file.
        A: xxxxxx_1.pdf          -> 1
        B: PagoPA0001_......pdf -> 1
        """
        name, _ = os.path.splitext(filename)
        # Caso PagoPA: PagoPA0003... -> 3
        m = re.search(r'PagoPA0*(\d+)', name, re.I)
        if m:
            return str(int(m.group(1)))   # "0003" -> "3"
        # Caso generico: ultimo gruppo numerico dopo underscore
        m = re.search(r'_(\d+)$', name)
        if m:
            return str(int(m.group(1)))   # "xxxx_007" -> "7"
        return None

    def merge_pdfs(self):
        current = self.merge_logic.get()
        if current == "progressive":
            a_paths = self.get_merge_files(self.merge_source_a)
            b_paths = self.get_merge_files(self.merge_source_b)
            if not a_paths and not b_paths:
                messagebox.showwarning("Attenzione", "Seleziona almeno una cartella per A e B.")
                return
        else:
            if not self.simple_merge_list:
                messagebox.showwarning("Attenzione", "Aggiungi almeno un file alla lista per l'unione semplice.")
                return

        out_dir = filedialog.askdirectory(title="Seleziona cartella dove salvare i PDF uniti")
        if not out_dir: return
        merged_folder = os.path.join(out_dir, "Uniti")
        os.makedirs(merged_folder, exist_ok=True)

        self.merge_log_text.config(state="normal")
        self.merge_log_text.delete(1.0, tk.END)
        self.merge_log_text.insert(tk.END, "--- Inizio Unione PDF ---\n")
        self.merge_log_text.insert(tk.END, f"Cartella destinazione: {merged_folder}\n\n")

        try:
            if current == "progressive":
                # COSTRUZIONE DIZIONARI
                avvisi = {}   # prog -> path A
                pagopa = {}   # prog -> path B
                for p in a_paths:
                    prog = self.extract_progressive_from_filename(os.path.basename(p))
                    if prog:
                        avvisi[prog] = p
                    else:
                        self.merge_log_text.insert(tk.END, f"⚠️ Ignorato (nessun progressivo): {os.path.basename(p)}\n")
                for p in b_paths:
                    prog = self.extract_progressive_from_filename(os.path.basename(p))
                    if prog:
                        pagopa[prog] = p
                    else:
                        self.merge_log_text.insert(tk.END, f"⚠️ Ignorato (nessun progressivo): {os.path.basename(p)}\n")
                common = sorted(set(avvisi) & set(pagopa))
                if not common:
                    messagebox.showwarning("Nessuna corrispondenza", "Nessun progressivo comune tra A e B.")
                    return
                self.merge_log_text.insert(tk.END, f"✅ Trovate {len(common)} coppie da unire\n\n")
                for prog in common:
                    avviso_path = avvisi[prog]
                    pagopa_path = pagopa[prog]
                    merger = PyPDF2.PdfMerger()
                    merger.append(avviso_path)
                    merger.append(pagopa_path)
                    out_name = os.path.basename(avviso_path)
                    out_path = os.path.join(merged_folder, out_name)
                    with open(out_path, "wb") as f_out:
                        merger.write(f_out)
                    merger.close()
                    self.merge_log_text.insert(tk.END, f"✅ {out_name}\n")
                self.merge_log_text.insert(tk.END, f"\n--- Unione completata: {len(common)} file in {merged_folder} ---")
                messagebox.showinfo("Completato", f"Creati {len(common)} PDF uniti in:\n{merged_folder}")
            else:
                # SEMPLICE
                out_name = "Merged_Output_Simple.pdf"
                out_path = os.path.join(merged_folder, out_name)
                counter = 1
                while os.path.exists(out_path):
                    out_name = f"Merged_Output_Simple_{counter}.pdf"
                    out_path = os.path.join(merged_folder, out_name)
                    counter += 1
                merger = PyPDF2.PdfMerger()
                for path, _, display_name in self.simple_merge_list:
                    merger.append(path)
                    self.merge_log_text.insert(tk.END, f"🔗 {display_name}\n")
                with open(out_path, "wb") as f_out:
                    merger.write(f_out)
                merger.close()
                self.merge_log_text.insert(tk.END, f"\n✅ File salvato: {out_name}")
                messagebox.showinfo("Completato", f"File unito salvato in:\n{out_path}")
        except Exception as e:
            self.merge_log_text.insert(tk.END, f"\n❌ ERRORE: {str(e)}\n")
            messagebox.showerror("Errore di Unione", f"Errore durante l'unione:\n{str(e)}")
        finally:
            self.merge_log_text.config(state="disabled")

    # ---------- ALTRE FUNZIONI ----------
    def select_file(self, section):
        if section in ("split", "rotate"):
            f = filedialog.askopenfilename(title="Seleziona PDF", filetypes=[("PDF files", "*.pdf")])
            if f: self.load_pdf(f, section)
        elif section in ("a", "b"):
            merge_type = getattr(self, f"merge_type_{section}").get()
            if merge_type == "folder":
                folder = filedialog.askdirectory(title=f"Cartella sorgente {section.upper()}")
                if folder: self.load_merge_source(folder, section, "folder")

    def on_drop(self, event, section):
        path = event.data.strip('{}')
        if path.lower().endswith('.pdf'):
            self.load_pdf(path, section)
        else:
            messagebox.showerror("Errore", "Seleziona un file PDF valido")

    def on_drop_merge(self, event, side):
        path = event.data.strip('{}')
        if os.path.isdir(path):
            self.load_merge_source(path, side, "folder")

    def load_pdf(self, path, section):
        self.pdf_path = path
        name = os.path.basename(path)
        if section == "split":
            self.file_label_split.config(text=f"✓ {name}", fg=self.colors['secondary'])
            self.drop_label_split.config(bg="#e8f7f9", fg=self.colors['secondary'])
            self.update_search_pattern_label()
        elif section == "rotate":
            self.file_label_rotate.config(text=f"✓ {name}", fg=self.colors['secondary'])
            self.rotate_btn.config(state="normal")
            self.drop_label_rotate.config(bg="#fff9e6", fg=self.colors['warning'])

    def load_merge_source(self, path, side, type_loaded):
        lbl = getattr(self, f"file_label_merge_{side}")
        drop = getattr(self, f"drop_label_merge_{side}")
        setattr(self, f"merge_source_{side}", path)
        lbl.config(text=f"✓ {os.path.basename(path)} ({type_loaded.capitalize()})", fg=self.colors['secondary'])
        drop.config(bg="#e8f5e9", fg=self.colors['secondary'])
        self.update_merge_log()

    # ---------- SPLIT ANALYSIS ----------
    def extract_custom_identifier(self, text):
        """
        Restituisce la porzione di testo che segue il marcatore.
        Il pattern dell’utente DEVE contenere almeno un gruppo di cattura
        (es. 'Numero avviso:\s*(.+)')
        """
        if not self.custom_search_string:
            return None
        try:
            match = re.search(self.custom_search_string, text, re.IGNORECASE)
            if match and match.groups():          # almeno un grupbo catturato
                identifier = match.group(1).strip()
                # pulisci caratteri illegali per il file-system
                return re.sub(r'[\\/:*?"<>|]', '_', identifier)
        except re.error:
            # fallback a semplice "contiene"
            idx = text.lower().find(self.custom_search_string.lower())
            if idx != -1:
                after = text[idx + len(self.custom_search_string):].strip().split()[0]
                return re.sub(r'[\\/:*?"<>|]', '_', after)
        return None

    def start_analysis(self):
        method = self.split_method.get()
        if method == "cf" and not self.custom_search_string:
            messagebox.showwarning("Attenzione", "Configura prima la stringa di ricerca.")
            return
        if method == "pages":
            try:
                n = int(self.pages_entry.get())
                if n <= 0: raise ValueError
            except ValueError:
                messagebox.showwarning("Attenzione", "Inserisci un numero valido di pagine.")
                return
        self.stop_analysis_flag = False
        self.analyze_btn.config(state="disabled")
        self.stop_btn.config(text="🛑 Blocca Scansione", state="normal")
        self.split_btn.config(state="disabled")
        self.root.after(100, self._run_analysis)

    def stop_analysis(self):
        self.stop_analysis_flag = True
        self.log_result("\n🛑 Segnale di interruzione ricevuto...")
        self.stop_btn.config(text="Interruzione in corso...", state="disabled")

    def _run_analysis(self):
        if not self.pdf_path: return
        method = self.split_method.get()
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.log_result("--- Inizio Analisi PDF ---")
        self.log_result(f"File: {os.path.basename(self.pdf_path)}")
        self.log_result(f"Metodo: {'Marcatore Personalizzato' if method == 'cf' else f'Ogni {self.pages_entry.get()} pagine'}\n")
        self.avvisi = []
        try:
            if method == "cf":
                self.analyze_by_cf()
            else:
                self.analyze_by_pages()
            if self.stop_analysis_flag:
                self.log_result("\n❌ ANALISI INTERROTTA.")
            else:
                self.log_result("\n--- Analisi Completata ---")
                if self.avvisi:
                    self.log_result(f"✅ Trovati {len(self.avvisi)} blocchi.")
                    self.log_result("*** Riepilogo ***")
                    for avv in self.avvisi:
                        np = avv['end'] - avv['start'] + 1
                        self.log_result(f"- Blocco {avv['progressivo']} ({np} pag.): ID: {avv['cf']} (Pagine {avv['start']+1}-{avv['end']+1})")
                    self.split_btn.config(state="normal")
                    messagebox.showinfo("Analisi Completata", f"Trovati {len(self.avvisi)} blocchi pronti per la divisione!")
                else:
                    self.log_result("❌ Nessun blocco trovato.")
                    messagebox.showwarning("Analisi Completata", "Nessun blocco trovato.")
        except Exception as e:
            self.log_result(f"❌ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante l'analisi:\n{str(e)}")
        finally:
            self.results_text.config(state="disabled")
            self.analyze_btn.config(state="normal")
            self.stop_btn.config(text="🛑 Blocca Scansione", state="disabled")

    def analyze_by_cf(self):
        if not self.custom_search_string:
            self.log_result("❌ Stringa personalizzata non configurata.")
            return
        
        with pdfplumber.open(self.pdf_path) as pdf:
            total = len(pdf.pages)
            self.log_result(f"Pagine totali: {total}")

            markers = []

            for i, page in enumerate(pdf.pages):
                if self.stop_analysis_flag:
                    break

                self.log_result(f"Scansione Pagina {i+1}...")
                text = page.extract_text() or ""

                ident = self.extract_custom_identifier(text)
                if ident:
                    markers.append({
                        'page': i,
                        'cf': ident
                    })
                    self.log_result(f"    ⭐ Marcatore trovato! ID: {ident}")
                else:
                    self.log_result(f"    ...Nessun marcatore trovato.")

            if not markers:
                self.log_result("❌ Nessun marcatore trovato.")
                return

            # costruzione blocchi
            self.avvisi = []
            for idx, m in enumerate(markers, 1):
                start = m['page']
                end = markers[idx]['page'] - 1 if idx < len(markers) else total - 1

                self.avvisi.append({
                    'progressivo': idx,
                    'cf': m['cf'],
                    'start': start,
                    'end': end
                })

            self.log_result(f"\nTrovati {len(self.avvisi)} blocchi.")


        


    def analyze_by_pages(self):
        try:
            n = int(self.pages_entry.get())
            if n <= 0: raise ValueError
        except ValueError:
            self.log_result("❌ Valore non valido per 'Divisione ogni pagine'.")
            return
        with open(self.pdf_path, 'rb') as f:
            reader = PyPDF2.PdfReader(f)
            total = len(reader.pages)
            self.log_result(f"Modalità: ogni {n} pagine. Pagine totali: {total}")
            self.avvisi = []
            block = 0
            start = 0
            while start < total:
                block += 1
                end = min(start + n - 1, total - 1)
                self.avvisi.append({'progressivo': block, 'cf': f"Block_{block}", 'start': start, 'end': end})
                self.log_result(f"✅ Blocco {block}: Pagine {start+1}-{end+1}")
                start = end + 1

    def split_pdf(self):
        if not self.pdf_path or not self.avvisi:
            messagebox.showwarning("Attenzione", "Esegui prima l'analisi.")
            return
        out_dir = filedialog.askdirectory(title="Cartella destinazione per i file divisi")
        if not out_dir: return
        base_name = os.path.splitext(os.path.basename(self.pdf_path))[0]
        self.results_text.config(state="normal")
        self.results_text.delete(1.0, tk.END)
        self.log_result(f"--- Divisione PDF in {len(self.avvisi)} file ---")
        self.log_result(f"Cartella: {out_dir}")
        try:
            reader = PyPDF2.PdfReader(self.pdf_path)
            for avv in self.avvisi:
                writer = PyPDF2.PdfWriter()
                raw_ident = avv.get('cf', f"Block_{avv['progressivo']}")
                ident = re.sub(r'[\\/:*?"<>|]', '_', raw_ident)
                ident = ident.strip()
                out_name = f"{base_name}_{avv['progressivo']}.pdf"
                out_path = os.path.join(out_dir, out_name)
                self.log_result(f"💾 {out_name} (Pagine {avv['start']+1}-{avv['end']+1})")
                for p in range(avv['start'], avv['end'] + 1):
                    writer.add_page(reader.pages[p])
                with open(out_path, 'wb') as f_out:
                    writer.write(f_out)
            self.log_result("\n--- Divisione Completata! ---")
            messagebox.showinfo("Completato", f"PDF diviso in {len(self.avvisi)} file in:\n{out_dir}")
        except Exception as e:
            self.log_result(f"❌ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante la divisione:\n{str(e)}")
        finally:
            self.results_text.config(state="disabled")

    def rotate_pdf(self):
        if not self.pdf_path:
            messagebox.showwarning("Attenzione", "Seleziona prima un PDF.")
            return
        base, ext = os.path.splitext(os.path.basename(self.pdf_path))
        out_path = filedialog.asksaveasfilename(defaultextension=".pdf", initialfile=f"{base}_ROTATED{ext}", title="Salva PDF ruotato", filetypes=[("PDF files", "*.pdf")])
        if not out_path: return
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.insert(tk.END, "--- Inizio Rotazione ---\n")
        try:
            reader = PyPDF2.PdfReader(self.pdf_path)
            writer = PyPDF2.PdfWriter()
            rotated = 0
            total = len(reader.pages)
            self.log_text.insert(tk.END, f"Pagine totali: {total}\n")
            for i in range(total):
                page = reader.pages[i]
                try:
                    w, h = float(page.mediabox.width), float(page.mediabox.height)
                except:
                    self.log_text.insert(tk.END, f"❌ Pagina {i+1} MediaBox non valido – saltata.\n")
                    writer.add_page(page)
                    continue
                self.log_text.insert(tk.END, f"Pagina {i+1}: {w:.0f}x{h:.0f}")
                if w > h:
                    page.rotate(270)
                    rotated += 1
                    self.log_text.insert(tk.END, " -> RUOTATA 270°\n")
                else:
                    self.log_text.insert(tk.END, " -> Verticale (nessuna rotazione)\n")
                writer.add_page(page)
            with open(out_path, 'wb') as f_out:
                writer.write(f_out)
            self.log_text.insert(tk.END, f"\n--- Rotazione Completata ---\n✅ {rotated} pagine ruotate su {total}")
            messagebox.showinfo("Completato", f"PDF ruotato salvato in:\n{out_path}")
        except Exception as e:
            self.log_text.insert(tk.END, f"\n❌ ERRORE: {str(e)}")
            messagebox.showerror("Errore", f"Errore durante la rotazione:\n{str(e)}")
        finally:
            self.log_text.config(state="disabled")

    def reset(self, section):
        if section == "split":
            self.pdf_path = None
            self.avvisi = []
            self.file_label_split.config(text="Nessun file selezionato", fg=self.colors['text_light'])
            self.drop_label_split.config(bg="#f0f7ff", fg=self.colors['text_light'])
            self.analyze_btn.config(state="disabled")
            self.split_btn.config(state="disabled")
            self.stop_btn.config(text="🛑 Blocca Scansione", state="disabled")
            self.results_text.config(state="normal")
            self.results_text.delete(1.0, tk.END)
            self.results_text.config(state="disabled")
            self.update_search_pattern_label()
        elif section == "rotate":
            self.pdf_path = None
            self.file_label_rotate.config(text="Nessun file selezionato", fg=self.colors['text_light'])
            self.drop_label_rotate.config(bg="#fffbf0", fg=self.colors['text_light'])
            self.rotate_btn.config(state="disabled")
            self.log_text.config(state="normal")
            self.log_text.delete(1.0, tk.END)
            self.log_text.config(state="disabled")
        elif section == "merge":
            self.merge_source_a = None
            self.merge_source_b = None
            if hasattr(self, 'file_label_merge_a'):
                self.file_label_merge_a.config(text="", fg=self.colors['text_light'])
                self.drop_label_merge_a.config(bg="#f3e5f5", fg=self.colors['text_light'])
                self.file_label_merge_b.config(text="", fg=self.colors['text_light'])
                self.drop_label_merge_b.config(bg="#f3e5f5", fg=self.colors['text_light'])
            self.simple_merge_list = []
            if hasattr(self, 'simple_merge_listbox'):
                self.simple_merge_listbox.delete(0, tk.END)
            self.merge_btn.config(state="disabled")
            self.update_merge_log()

    # ---------- UI EXTRAS ----------
    def on_method_change(self):
        if self.split_method.get() == "pages":
            self.pages_entry.config(state="normal")
            self.custom_string_btn.config(state="disabled")
        else:
            self.pages_entry.config(state="disabled")
            self.custom_string_btn.config(state="normal")
        self.update_search_pattern_label()

    def configure_search_string(self):
        popup = tk.Toplevel(self.root)
        popup.title("Configura Stringa/RegEx di ricerca")
        popup.geometry("600x300")
        popup.transient(self.root)
        popup.grab_set()
        popup.update_idletasks()
        x = (popup.winfo_screenwidth() // 2) - (600 // 2)
        y = (popup.winfo_screenheight() // 2) - (300 // 2)
        popup.geometry(f"600x300+{x}+{y}")
        main_frame = tk.Frame(popup, bg=self.colors['light_bg'], padx=20, pady=20)
        main_frame.pack(fill="both", expand=True)
        tk.Label(main_frame, text="🔍 Inserisci il Marcatore di Divisione", font=("Segoe UI", 14, "bold"), bg=self.colors['light_bg'], fg=self.colors['text_dark']).pack(pady=(0, 15))
        custom_frame = tk.Frame(main_frame, bg=self.colors['card_bg'], relief="solid", bd=1)
        custom_frame.pack(fill="x", expand=True, pady=(0, 10))
        custom_content = tk.Frame(custom_frame, bg=self.colors['card_bg'], padx=15, pady=10)
        custom_content.pack(fill="both", expand=True)
        tk.Label(custom_content, text="Stringa o Espressione Regolare (RegEx):", font=("Segoe UI", 10, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 8))
        custom_entry = tk.Entry(custom_content, font=("Segoe UI", 10), relief="solid", bd=1)
        custom_entry.pack(fill="x", ipady=4)
        custom_entry.insert(0, r"Numero avviso:\s*(\S+)")
        if self.custom_search_string:
            custom_entry.insert(0, self.custom_search_string)
        tk.Label(custom_content, text=r"💡 Inserisci la stringa esatta che marca l'inizio di ogni blocco (es: 'Numero avviso:', 'C.F. XYZ').\nPuoi usare RegEx per marcatori variabili (es: C\.F\.\s*[:/]?\s*([A-Z0-9]{11,16}))", font=("Segoe UI", 8, "italic"), bg=self.colors['card_bg'], fg=self.colors['text_light'], justify="left").pack(anchor="w", pady=(5, 0))
        button_frame = tk.Frame(main_frame, bg=self.colors['light_bg'])
        button_frame.pack(pady=10)
        def save():
            s = custom_entry.get().strip()
            if not s:
                messagebox.showwarning("Attenzione", "Inserisci una stringa valida!", parent=popup)
                return
            self.custom_search_string = s
            self.update_search_pattern_label()
            popup.destroy()
        tk.Button(button_frame, text="✓ Salva e Applica", command=save, font=("Segoe UI", 10, "bold"), bg=self.colors['secondary'], fg="white", padx=20, pady=8, relief="flat", cursor="hand2", border=0).pack(side="left", padx=5)
        tk.Button(button_frame, text="✗ Annulla", command=popup.destroy, font=("Segoe UI", 10, "bold"), bg=self.colors['text_light'], fg="white", padx=20, pady=8, relief="flat", cursor="hand2", border=0).pack(side="left", padx=5)

    def update_search_pattern_label(self):
        if self.custom_search_string:
            display = self.custom_search_string if len(self.custom_search_string) < 30 else self.custom_search_string[:27] + "..."
            self.search_pattern_label.config(text=f'"{display}"', fg=self.colors['primary'])
            if self.pdf_path and self.split_method.get() == "cf":
                self.analyze_btn.config(state="normal")
            elif self.pdf_path and self.split_method.get() == "pages":
                self.analyze_btn.config(state="normal")
            else:
                self.analyze_btn.config(state="disabled")
        else:
            self.search_pattern_label.config(text="(Non configurato)", fg=self.colors['danger'])
            if self.pdf_path and self.split_method.get() == "pages":
                self.analyze_btn.config(state="normal")
            else:
                self.analyze_btn.config(state="disabled")

    def log_result(self, message):
        self.results_text.config(state="normal")
        self.results_text.insert(tk.END, message + "\n")
        self.results_text.yview(tk.END)
        self.results_text.config(state="disabled")
        self.root.update_idletasks()

    # ---------- SEMPLICE MERGE EXTRAS ----------
    def select_file_simple(self, item_type):
        if item_type == "file":
            paths = filedialog.askopenfilenames(title="Aggiungi PDF", filetypes=[("PDF files", "*.pdf")])
            for p in paths: self.add_simple_merge_item(p, "file")
        else:
            path = filedialog.askdirectory(title="Aggiungi cartella PDF")
            if path: self.add_simple_merge_item(path, "folder")

    def on_drop_merge_simple(self, event):
        paths = self._parse_dnd_paths(event.data)
        for p in paths:
            if os.path.isdir(p):
                self.add_simple_merge_item(p, "folder")
            elif os.path.isfile(p) and p.lower().endswith('.pdf'):
                self.add_simple_merge_item(p, "file")

    def add_simple_merge_item(self, path, item_type):
        if item_type == "folder":
            files = self.get_merge_files(path)
            if not files:
                messagebox.showwarning("Attenzione", f"Nessun PDF trovato in:\n{os.path.basename(path)}")
                return
            new_items = [(f, "file", os.path.basename(f)) for f in files]
        else:
            new_items = [(path, "file", os.path.basename(path))]
        for item in new_items:
            if item not in self.simple_merge_list:
                self.simple_merge_list.append(item)
                self.simple_merge_listbox.insert(tk.END, f"📄 {item[2]}")
        self.update_merge_log()

    def remove_simple_merge_item(self):
        try:
            idx = self.simple_merge_listbox.curselection()[0]
            self.simple_merge_listbox.delete(idx)
            del self.simple_merge_list[idx]
            self.update_merge_log()
        except IndexError:
            messagebox.showwarning("Attenzione", "Seleziona un elemento da rimuovere.")

    def move_simple_merge_item(self, direction):
        try:
            idx = self.simple_merge_listbox.curselection()[0]
            new_idx = idx + direction
            if 0 <= new_idx < len(self.simple_merge_list):
                item_data = self.simple_merge_list.pop(idx)
                self.simple_merge_list.insert(new_idx, item_data)
                txt = self.simple_merge_listbox.get(idx)
                self.simple_merge_listbox.delete(idx)
                self.simple_merge_listbox.insert(new_idx, txt)
                self.simple_merge_listbox.selection_set(new_idx)
                self.simple_merge_listbox.see(new_idx)
                self.update_merge_log()
        except IndexError:
            messagebox.showwarning("Attenzione", "Seleziona un elemento da spostare.")

    def _parse_dnd_paths(self, data):
        data = data.strip('{}')
        paths, cur, in_braces = [], "", False
        for ch in data:
            if ch == '{':
                in_braces = True
                cur = ""
            elif ch == '}':
                in_braces = False
                if cur: paths.append(cur)
                cur = ""
            elif ch == ' ' and not in_braces:
                if cur: paths.append(cur); cur = ""
            else:
                cur += ch
        if cur: paths.append(cur)
        return paths if paths else [data]
    
    def setup_rename_section(self):
        self.rename_frame = tk.Frame(self.container, bg=self.colors['light_bg'])

        # Intestazione
        header = tk.Frame(self.rename_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        header.pack(fill="x", pady=(0, 15))
        tk.Frame(header, bg='#ff9800', height=10).pack(fill="x")
        head_content = tk.Frame(header, bg=self.colors['card_bg'])
        head_content.pack(fill="x", padx=20, pady=15)
        tk.Label(head_content, text="✏️ Rinomina PDF", font=("Segoe UI", 14, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w")
        tk.Label(head_content, text="Carica una cartella o dei file PDF e scegli il nome base.\nI file verranno rinominati come base_1.pdf, base_2.pdf, ...", font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text_light'], justify="left").pack(anchor="w", pady=(5, 0))

        # Drop area
        drop_card = tk.Frame(self.rename_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        drop_card.pack(fill="x", pady=(0, 15))
        tk.Frame(drop_card, bg='#ff9800', height=8).pack(fill="x")
        drop_content = tk.Frame(drop_card, bg=self.colors['card_bg'])
        drop_content.pack(fill="both", expand=True, padx=25, pady=20)
        self.drop_label_rename = tk.Label(drop_content, text="📁 Trascina cartella o PDF oppure clicca", font=("Segoe UI", 12), bg="#fff3e0", fg=self.colors['text_light'], relief="solid", bd=2, height=3, cursor="hand2")
        self.drop_label_rename.pack(fill="both", expand=True)
        self.drop_label_rename.drop_target_register(DND_FILES)
        self.drop_label_rename.dnd_bind('<<Drop>>', self.on_drop_rename)
        self.drop_label_rename.bind('<Button-1>', lambda e: self.select_rename_source())
        self.rename_list_lbl = tk.Label(drop_content, text="Nessun file selezionato", fg=self.colors['text_light'], bg=self.colors['card_bg'], font=("Segoe UI", 10))
        self.rename_list_lbl.pack(pady=(10, 0))

        # Base name
        base_frame = tk.Frame(self.rename_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        base_frame.pack(fill="x", pady=(0, 15))
        tk.Frame(base_frame, bg='#ff9800', height=8).pack(fill="x")
        base_content = tk.Frame(base_frame, bg=self.colors['card_bg'])
        base_content.pack(fill="x", padx=20, pady=15)
        tk.Label(base_content, text="📝 Nome base per i file rinominati", font=("Segoe UI", 12, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 8))
        base_entry = tk.Entry(base_content, textvariable=self.current_rename_base, font=("Segoe UI", 11), relief="solid", bd=1)
        base_entry.pack(fill="x", ipady=6)
        tk.Label(base_content, text="I file verranno rinominati come: base_1.pdf, base_2.pdf, ...", font=("Segoe UI", 9), bg=self.colors['card_bg'], fg=self.colors['text_light']).pack(anchor="w", pady=(5, 0))
        self.current_rename_base.trace_add("write", lambda *args: self.update_rename_preview())

        # Preview
        preview_card = tk.Frame(self.rename_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        preview_card.pack(fill="both", expand=True, pady=(0, 15))
        tk.Frame(preview_card, bg='#ff9800', height=8).pack(fill="x")
        preview_content = tk.Frame(preview_card, bg=self.colors['card_bg'])
        preview_content.pack(fill="both", expand=True, padx=20, pady=15)
        tk.Label(preview_content, text="👁️ Anteprima rinominazione", font=("Segoe UI", 12, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 8))
        self.rename_preview_text = scrolledtext.ScrolledText(preview_content, height=6, font=("Consolas", 9), state="disabled", relief="flat", bg="#f8f9fa", wrap="word")
        self.rename_preview_text.pack(fill="both", expand=True)

        # Bottoni
        btn_frame = tk.Frame(self.rename_frame, bg=self.colors['light_bg'])
        btn_frame.pack(pady=10)
        self.rename_start_btn = tk.Button(btn_frame, text="✅ Rinomina", command=self.start_rename, state="disabled", font=("Segoe UI", 11, "bold"), bg='#ff9800', fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.rename_start_btn.pack(side="left", padx=6)
        self.rename_reset_btn = tk.Button(btn_frame, text="🔄 Reset", command=self.reset_rename, font=("Segoe UI", 11, "bold"), bg=self.colors['text_light'], fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.rename_reset_btn.pack(side="left", padx=6)

    def on_drop_rename(self, event):
        paths = self._parse_dnd_paths(event.data)
        new_files = []
        for p in paths:
            if os.path.isdir(p):
                new_files.extend(self.get_merge_files(p))
            elif p.lower().endswith('.pdf'):
                new_files.append(p)
        if new_files:
            self.rename_source_paths = list(dict.fromkeys(new_files))  # uniq
            self.update_rename_preview()

    def select_rename_source(self):
        # Scelta multipla: file o cartella
        choice = messagebox.askquestion("Scegli", "Vuoi selezionare una cartella?", icon='question')
        if choice == 'yes':
            folder = filedialog.askdirectory(title="Seleziona cartella PDF")
            if folder:
                self.rename_source_paths = self.get_merge_files(folder)
                self.update_rename_preview()
        else:
            files = filedialog.askopenfilenames(title="Seleziona PDF", filetypes=[("PDF files", "*.pdf")])
            if files:
                self.rename_source_paths = list(files)
                self.update_rename_preview()

    def update_rename_preview(self):
        self.rename_list_lbl.config(text=f"{len(self.rename_source_paths)} file selezionati")
        self.drop_label_rename.config(bg="#e8f5e9", fg=self.colors['secondary'])

        self.rename_preview_text.config(state="normal")
        self.rename_preview_text.delete(1.0, tk.END)
        if not self.rename_source_paths:
            self.rename_preview_text.insert(tk.END, "Nessun file da rinominare.\n")
            self.rename_start_btn.config(state="disabled")
            self.rename_preview_text.config(state="disabled")
            return

        base = self.current_rename_base.get().strip() or "Documento"
        self.rename_preview_text.insert(tk.END, f"Nome base: {base}\n")
        self.rename_preview_text.insert(tk.END, "Anteprima nuovi nomi:\n\n")
        for idx, path in enumerate(self.rename_source_paths, 1):
            old = os.path.basename(path)
            new = f"{base}_{idx}.pdf"
            self.rename_preview_text.insert(tk.END, f"{old}\n  ➜  {new}\n")
        self.rename_start_btn.config(state="normal")
        self.rename_preview_text.config(state="disabled")
    
    def start_rename(self):
        if not self.rename_source_paths:
            messagebox.showwarning("Attenzione", "Nessun file da rinominare.")
            return
        out_dir = filedialog.askdirectory(title="Seleziona dove salvare i file rinominati")
        if not out_dir: return
        rename_folder = os.path.join(out_dir, "Rinominati")
        os.makedirs(rename_folder, exist_ok=True)

        base = self.current_rename_base.get().strip() or "Documento"
        self.rename_preview_text.config(state="normal")
        self.rename_preview_text.insert(tk.END, f"\n--- Inizio rinominazione ---\n")
        try:
            for idx, old_path in enumerate(self.rename_source_paths, 1):
                new_name = f"{base}_{idx}.pdf"
                new_path = os.path.join(rename_folder, new_name)
                with open(old_path, 'rb') as f_in, open(new_path, 'wb') as f_out:
                    f_out.write(f_in.read())
                self.rename_preview_text.insert(tk.END, f"✅ {new_name}\n")
            self.rename_preview_text.insert(tk.END, f"\n--- Rinominazione completata! ---\n")
            messagebox.showinfo("Completato", f"{len(self.rename_source_paths)} file rinominati in:\n{rename_folder}")
        except Exception as e:
            self.rename_preview_text.insert(tk.END, f"❌ ERRORE: {str(e)}\n")
            messagebox.showerror("Errore", f"Errore durante la rinominazione:\n{str(e)}")
        finally:
            self.rename_preview_text.config(state="disabled")
    
    def reset_rename(self):
        self.rename_source_paths.clear()
        self.current_rename_base.set("Documento")
        self.rename_list_lbl.config(text="Nessun file selezionato")
        self.drop_label_rename.config(bg="#fff3e0", fg=self.colors['text_light'])
        self.rename_preview_text.config(state="normal")
        self.rename_preview_text.delete(1.0, tk.END)
        self.rename_preview_text.insert(tk.END, "Trascina file/cartella per iniziare.\n")
        self.rename_preview_text.config(state="disabled")
        self.rename_start_btn.config(state="disabled")

    def setup_split250_section(self):
        self.split250_frame = tk.Frame(self.container, bg=self.colors['light_bg'])

        # intestazione
        head = tk.Frame(self.split250_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        head.pack(fill="x", pady=(0, 15))
        tk.Frame(head, bg='#00bcd4', height=10).pack(fill="x")
        head_content = tk.Frame(head, bg=self.colors['card_bg'])
        head_content.pack(fill="x", padx=20, pady=15)
        tk.Label(head_content, text="📦 Split-250", font=("Segoe UI", 14, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w")
        tk.Label(head_content, text="Trascina una cartella contenente PDF.\nI file verranno divisi in blocchi da 250 in sottocartelle 1-250, 251-500, ...", font=("Segoe UI", 10), bg=self.colors['card_bg'], fg=self.colors['text_light'], justify="left").pack(anchor="w", pady=(5, 0))

        # drop area
        drop_card = tk.Frame(self.split250_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        drop_card.pack(fill="x", pady=(0, 15))
        tk.Frame(drop_card, bg='#00bcd4', height=8).pack(fill="x")
        drop_content = tk.Frame(drop_card, bg=self.colors['card_bg'])
        drop_content.pack(fill="both", expand=True, padx=25, pady=20)
        self.drop_label_split250 = tk.Label(drop_content, text="📁 Trascina cartella PDF o clicca", font=("Segoe UI", 12), bg="#e0f7fa", fg=self.colors['text_light'], relief="solid", bd=2, height=3, cursor="hand2")
        self.drop_label_split250.pack(fill="both", expand=True)
        self.drop_label_split250.drop_target_register(DND_FILES)
        self.drop_label_split250.dnd_bind('<<Drop>>', self.on_drop_split250)
        self.drop_label_split250.bind('<Button-1>', lambda e: self.select_split250_folder())
        self.split250_list_lbl = tk.Label(drop_content, text="Nessuna cartella selezionata", fg=self.colors['text_light'], bg=self.colors['card_bg'], font=("Segoe UI", 10))
        self.split250_list_lbl.pack(pady=(10, 0))

        # anteprima / log
        log_card = tk.Frame(self.split250_frame, bg=self.colors['card_bg'], relief="flat", bd=0)
        log_card.pack(fill="both", expand=True, pady=(0, 15))
        tk.Frame(log_card, bg='#00bcd4', height=8).pack(fill="x")
        log_content = tk.Frame(log_card, bg=self.colors['card_bg'])
        log_content.pack(fill="both", expand=True, padx=20, pady=15)
        tk.Label(log_content, text="📋 Anteprima blocchi", font=("Segoe UI", 12, "bold"), bg=self.colors['card_bg'], fg=self.colors['text_dark']).pack(anchor="w", pady=(0, 8))
        self.split250_log = scrolledtext.ScrolledText(log_content, height=6, font=("Consolas", 9), state="disabled", relief="flat", bg="#f8f9fa", wrap="word")
        self.split250_log.pack(fill="both", expand=True)

        # bottoni
        btn_frame = tk.Frame(self.split250_frame, bg=self.colors['light_bg'])
        btn_frame.pack(pady=10)
        self.split250_start_btn = tk.Button(btn_frame, text="✅ Crea blocchi", command=self.start_split250, state="disabled", font=("Segoe UI", 11, "bold"), bg='#00bcd4', fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.split250_start_btn.pack(side="left", padx=6)
        self.split250_reset_btn = tk.Button(btn_frame, text="🔄 Reset", command=self.reset_split250, font=("Segoe UI", 11, "bold"), bg=self.colors['text_light'], fg="white", padx=25, pady=12, relief="flat", cursor="hand2", border=0)
        self.split250_reset_btn.pack(side="left", padx=6)

    def on_drop_split250(self, event):
        paths = self._parse_dnd_paths(event.data)
        for p in paths:
            if os.path.isdir(p):
                self.load_split250_folder(p)
                return
            elif p.lower().endswith('.pdf'):
                messagebox.showwarning("Cartella richiesta", "Trascina una cartella, non file singoli.")
                return
    
    def select_split250_folder(self):
        folder = filedialog.askdirectory(title="Seleziona cartella con PDF")
        if folder:
            self.load_split250_folder(folder)

    def load_split250_folder(self, folder):
        self.split250_source_folder = folder
        self.split250_pdf_list = self.get_merge_files(folder)   # usa la stessa helper
        self.split250_list_lbl.config(text=f"{len(self.split250_pdf_list)} PDF trovati")
        self.drop_label_split250.config(bg="#e8f5e9", fg=self.colors['secondary'])
        self.update_split250_preview()

    def update_split250_preview(self):
        self.split250_log.config(state="normal")
        self.split250_log.delete(1.0, tk.END)
        if not self.split250_pdf_list:
            self.split250_log.insert(tk.END, "Nessun PDF da elaborare.\n")
            self.split250_start_btn.config(state="disabled")
            self.split250_log.config(state="disabled")
            return

        total = len(self.split250_pdf_list)
        block_size = 250
        blocks = (total - 1) // block_size + 1
        self.split250_log.insert(tk.END, f"PDF totali: {total}  –  blocchi da {block_size} file\n\n")
        for b in range(blocks):
            start = b * block_size + 1
            end = min((b + 1) * block_size, total)
            folder_name = f"{start}-{end}"
            self.split250_log.insert(tk.END, f"📂 {folder_name}  ({end - start + 1} file)\n")
        self.split250_start_btn.config(state="normal")
        self.split250_log.config(state="disabled")

    def start_split250(self):
        if not self.split250_pdf_list:
            messagebox.showwarning("Attenzione", "Nessun PDF da elaborare.")
            return
        out_dir = filedialog.askdirectory(title="Seleziona dove salvare i blocchi")
        if not out_dir: return
        split250_root = os.path.join(out_dir, "Split_250")
        os.makedirs(split250_root, exist_ok=True)

        self.split250_log.config(state="normal")
        self.split250_log.insert(tk.END, "\n--- Inizio creazione blocchi ---\n")
        try:
            total = len(self.split250_pdf_list)
            block_size = 250
            for idx, old_path in enumerate(self.split250_pdf_list, 1):
                block_num = (idx - 1) // block_size
                start = block_num * block_size + 1
                end = min((block_num + 1) * block_size, total)
                folder_name = f"{start}-{end}"
                dest_folder = os.path.join(split250_root, folder_name)
                os.makedirs(dest_folder, exist_ok=True)
                new_name = f"{idx}.pdf"
                shutil.copy(old_path, os.path.join(dest_folder, new_name))
                self.split250_log.insert(tk.END, f"✅ {folder_name}\\{new_name}\n")
            self.split250_log.insert(tk.END, f"\n--- Blocchi creati in: {split250_root} ---\n")
            messagebox.showinfo("Completato", f"Creati {((total-1)//block_size)+1} blocchi in:\n{split250_root}")
        except Exception as e:
            self.split250_log.insert(tk.END, f"❌ ERRORE: {str(e)}\n")
            messagebox.showerror("Errore", f"Errore durante la creazione blocchi:\n{str(e)}")
        finally:
            self.split250_log.config(state="disabled")

    def reset_split250(self):
        self.split250_source_folder = None
        self.split250_pdf_list.clear()
        self.split250_list_lbl.config(text="Nessuna cartella selezionata")
        self.drop_label_split250.config(bg="#fff3e0", fg=self.colors['text_light'])
        self.split250_log.config(state="normal")
        self.split250_log.delete(1.0, tk.END)
        self.split250_log.insert(tk.END, "Trascina una cartella per iniziare.\n")
        self.split250_log.config(state="disabled")
        self.split250_start_btn.config(state="disabled")

    def toggle_side_menu(self):
        """Apre / chiude il menù laterale togliendolo/ri-mettilo con pack."""
        if self.menu_open:
            # chiudi
            self.side_menu.pack_forget()
            self.menu_open = False
        else:
            # apri
            self.side_menu.pack(side="left", fill="y")
            self.side_menu.config(width=180)   # larghezza fissa quando è visibile
            self.menu_open = True
            
    def show_section(self, section):
        self.current_section = section
        # nascondi tutti i frame
        for frm in (self.split_frame, self.rotate_frame, self.merge_frame,
                    self.rename_frame, self.split250_frame):
            frm.pack_forget()

        # colora solo il bottone attivo (btn_list è la lista dei 5 pulsanti del menù)
        colors = ["#1a73e8", "#fbbc04", "#9c27b0", "#ff9800", "#00bcd4"]
        secs   = ["split",   "rotate",  "merge",  "rename",  "split250"]
        for btn, sec, col in zip(self.btn_list, secs, colors):
            btn.config(bg=col if sec == section else self.colors['dark'])

        # mostra il frame corrispondente
        {"split":   self.split_frame,
         "rotate":  self.rotate_frame,
         "merge":   self.merge_frame,
         "rename":  self.rename_frame,
         "split250":self.split250_frame}[section].pack(fill="both", expand=True)



if __name__ == '__main__':
    try:
        root = TkinterDnD.Tk()
    except Exception:
        root = tk.Tk()
        messagebox.showerror("Errore Libreria", "TkinterDnD non caricato – drag-and-drop disabilitato.")
    app = PDFToolApp(root)
    root.mainloop()