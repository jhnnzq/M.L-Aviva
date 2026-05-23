import flet as ft
import mysql.connector
from mysql.connector import pooling
from dotenv import load_dotenv
import os, hashlib, calendar
from datetime import datetime, date

load_dotenv()

# ══════════════════════════════════════════════════════
#  POOL DE CONEXÕES
# ══════════════════════════════════════════════════════

_pool = None

def get_pool():
    global _pool
    if _pool is None:
        _pool = pooling.MySQLConnectionPool(
            pool_name="aviva_pool",
            pool_size=5,
            host=os.getenv("DB_HOST"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"),
            database=os.getenv("DB_NAME"),
            port=int(os.getenv("DB_PORT", 52168)),
        )
    return _pool

def get_connection():
    return get_pool().get_connection()

# ══════════════════════════════════════════════════════
#  BANCO DE DADOS
# ══════════════════════════════════════════════════════

def init_db():
    conn = get_connection(); c = conn.cursor()
    c.execute("""CREATE TABLE IF NOT EXISTS usuarios(
        id_user INT PRIMARY KEY AUTO_INCREMENT,
        nm_user VARCHAR(50) NOT NULL,
        pass_user VARCHAR(255) NOT NULL,
        nivel_user TINYINT(1) NOT NULL,
        foto_user VARCHAR(255) DEFAULT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS funcoes(
        id_funcao INT PRIMARY KEY AUTO_INCREMENT,
        nm_funcao VARCHAR(50) NOT NULL)""")
    c.execute("""CREATE TABLE IF NOT EXISTS usuario_funcao(
        id_user INT NOT NULL, id_funcao INT NOT NULL,
        PRIMARY KEY(id_user,id_funcao),
        FOREIGN KEY(id_user) REFERENCES usuarios(id_user),
        FOREIGN KEY(id_funcao) REFERENCES funcoes(id_funcao))""")
    c.execute("""CREATE TABLE IF NOT EXISTS escalas(
        id_escala INT PRIMARY KEY AUTO_INCREMENT,
        dt_escala DATE NOT NULL, hr_escala VARCHAR(10),
        nm_escala VARCHAR(100), nova TINYINT(1) NOT NULL DEFAULT 1)""")
    c.execute("""CREATE TABLE IF NOT EXISTS escala_membros(
        id INT PRIMARY KEY AUTO_INCREMENT,
        id_escala INT NOT NULL, id_user INT NOT NULL, id_funcao INT,
        status VARCHAR(20) NOT NULL DEFAULT 'pendente', justif TEXT,
        FOREIGN KEY(id_escala) REFERENCES escalas(id_escala),
        FOREIGN KEY(id_user) REFERENCES usuarios(id_user))""")
    c.execute("""CREATE TABLE IF NOT EXISTS musicas(
        id_musica INT PRIMARY KEY AUTO_INCREMENT,
        nm_musica VARCHAR(100) NOT NULL, tom VARCHAR(10),
        link_cifra TEXT, link_letra TEXT, link_video TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS escala_musicas(
        id_escala INT NOT NULL, id_musica INT NOT NULL,
        PRIMARY KEY(id_escala,id_musica),
        FOREIGN KEY(id_escala) REFERENCES escalas(id_escala),
        FOREIGN KEY(id_musica) REFERENCES musicas(id_musica))""")
    try:
        c.execute("ALTER TABLE usuarios ADD COLUMN foto_user VARCHAR(255) DEFAULT NULL")
        conn.commit()
    except Exception:
        pass
    conn.commit(); c.close(); conn.close()

def criptografar(s): return hashlib.sha256(s.encode()).hexdigest()

def db_login(nome, senha):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT id_user,nm_user,nivel_user FROM usuarios WHERE nm_user=%s AND pass_user=%s",
              (nome, criptografar(senha)))
    r = c.fetchone(); c.close(); conn.close(); return r

def db_cadastrar(nome, senha, nivel=0):
    if len(senha) < 8: return "Senha deve ter no mínimo 8 caracteres"
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT id_user FROM usuarios WHERE nm_user=%s", (nome,))
    if c.fetchone(): c.close(); conn.close(); return "Usuário já existe"
    c.execute("INSERT INTO usuarios(nm_user,pass_user,nivel_user)VALUES(%s,%s,%s)",
              (nome, criptografar(senha), nivel))
    conn.commit(); c.close(); conn.close(); return "ok"

def db_membros():
    conn = get_connection(); c = conn.cursor()
    c.execute("""SELECT u.id_user, u.nm_user, u.nivel_user,
        GROUP_CONCAT(f.nm_funcao SEPARATOR ', '), u.foto_user
        FROM usuarios u
        LEFT JOIN usuario_funcao uf ON u.id_user=uf.id_user
        LEFT JOIN funcoes f ON uf.id_funcao=f.id_funcao
        GROUP BY u.id_user ORDER BY u.nm_user""")
    r = c.fetchall(); c.close(); conn.close(); return r

def db_funcoes():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT id_funcao,nm_funcao FROM funcoes ORDER BY nm_funcao")
    r = c.fetchall(); c.close(); conn.close(); return r

def db_add_funcao(nm):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO funcoes(nm_funcao)VALUES(%s)", (nm,))
    conn.commit(); c.close(); conn.close()

def db_atribuir_funcao(id_u, id_f):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO usuario_funcao(id_user,id_funcao)VALUES(%s,%s)", (id_u, id_f))
        conn.commit()
    except Exception:
        pass
    c.close(); conn.close()

def db_remover_membro(id_u):
    conn = get_connection(); c = conn.cursor()
    for q in ["DELETE FROM usuario_funcao WHERE id_user=%s",
              "DELETE FROM escala_membros WHERE id_user=%s",
              "DELETE FROM usuarios WHERE id_user=%s"]:
        c.execute(q, (id_u,))
    conn.commit(); c.close(); conn.close()

def db_salvar_foto(id_u, caminho):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE usuarios SET foto_user=%s WHERE id_user=%s", (caminho, id_u))
    conn.commit(); c.close(); conn.close()

def db_escalas():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT id_escala,dt_escala,hr_escala,nm_escala,nova FROM escalas ORDER BY dt_escala DESC")
    r = c.fetchall(); c.close(); conn.close(); return r

def db_contar_novas():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT COUNT(*) FROM escalas WHERE nova=1")
    r = c.fetchone(); c.close(); conn.close()
    return r[0] if r else 0

def db_criar_escala(dt, hr, nm):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO escalas(dt_escala,hr_escala,nm_escala)VALUES(%s,%s,%s)", (dt, hr, nm))
    conn.commit(); c.close(); conn.close()

def db_deletar_escala(id_e):
    conn = get_connection(); c = conn.cursor()
    for q in ["DELETE FROM escala_musicas WHERE id_escala=%s",
              "DELETE FROM escala_membros WHERE id_escala=%s",
              "DELETE FROM escalas WHERE id_escala=%s"]:
        c.execute(q, (id_e,))
    conn.commit(); c.close(); conn.close()

def db_membros_escala(id_e):
    conn = get_connection(); c = conn.cursor()
    c.execute("""SELECT em.id,u.nm_user,f.nm_funcao,em.status,em.justif,u.id_user
        FROM escala_membros em
        JOIN usuarios u ON em.id_user=u.id_user
        LEFT JOIN funcoes f ON em.id_funcao=f.id_funcao
        WHERE em.id_escala=%s""", (id_e,))
    r = c.fetchall(); c.close(); conn.close(); return r

def db_add_membro_escala(id_e, id_u, id_f=None):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT id FROM escala_membros WHERE id_escala=%s AND id_user=%s", (id_e, id_u))
    if not c.fetchone():
        c.execute("INSERT INTO escala_membros(id_escala,id_user,id_funcao)VALUES(%s,%s,%s)",
                  (id_e, id_u, id_f))
        conn.commit()
    c.close(); conn.close()

def db_rem_membro_escala(id_em):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM escala_membros WHERE id=%s", (id_em,))
    conn.commit(); c.close(); conn.close()

def db_responder(id_em, status, justif=""):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE escala_membros SET status=%s,justif=%s WHERE id=%s", (status, justif, id_em))
    conn.commit(); c.close(); conn.close()

def db_marcar_vista(id_e):
    conn = get_connection(); c = conn.cursor()
    c.execute("UPDATE escalas SET nova=0 WHERE id_escala=%s", (id_e,))
    conn.commit(); c.close(); conn.close()

def db_status_escala(id_e):
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT status FROM escala_membros WHERE id_escala=%s", (id_e,))
    rows = c.fetchall(); c.close(); conn.close()
    return sum(1 for r in rows if r[0] == "confirmado"), len(rows)

def db_musicas_escala(id_e):
    conn = get_connection(); c = conn.cursor()
    c.execute("""SELECT m.id_musica,m.nm_musica,m.tom,m.link_cifra,m.link_letra,m.link_video
        FROM musicas m JOIN escala_musicas em ON m.id_musica=em.id_musica
        WHERE em.id_escala=%s""", (id_e,))
    r = c.fetchall(); c.close(); conn.close(); return r

def db_todas_musicas():
    conn = get_connection(); c = conn.cursor()
    c.execute("SELECT id_musica,nm_musica,tom,link_cifra,link_letra,link_video FROM musicas ORDER BY nm_musica")
    r = c.fetchall(); c.close(); conn.close(); return r

def db_add_musica(nm, tom, cifra, letra, video):
    conn = get_connection(); c = conn.cursor()
    c.execute("INSERT INTO musicas(nm_musica,tom,link_cifra,link_letra,link_video)VALUES(%s,%s,%s,%s,%s)",
              (nm, tom, cifra, letra, video))
    conn.commit(); mid = c.lastrowid; c.close(); conn.close(); return mid

def db_vincular_musica(id_e, id_m):
    conn = get_connection(); c = conn.cursor()
    try:
        c.execute("INSERT INTO escala_musicas(id_escala,id_musica)VALUES(%s,%s)", (id_e, id_m))
        conn.commit()
    except Exception:
        pass
    c.close(); conn.close()

def db_desvincular_musica(id_e, id_m):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM escala_musicas WHERE id_escala=%s AND id_musica=%s", (id_e, id_m))
    conn.commit(); c.close(); conn.close()

def db_deletar_musica(id_m):
    conn = get_connection(); c = conn.cursor()
    c.execute("DELETE FROM escala_musicas WHERE id_musica=%s", (id_m,))
    c.execute("DELETE FROM musicas WHERE id_musica=%s", (id_m,))
    conn.commit(); c.close(); conn.close()

# ══════════════════════════════════════════════════════
#  CORES
# ══════════════════════════════════════════════════════
BG   = "#1A1A2E"
CARD = "#16213E"
C2   = "#0F3460"
AC   = "#E94560"
TX   = "#EAEAEA"
SB   = "#A0A0B0"
VD   = "#4CAF50"
AM   = "#FFC107"
VM   = "#F44336"

# ══════════════════════════════════════════════════════
#  MAIN
# ══════════════════════════════════════════════════════

def main(page: ft.Page):
    page.title        = "M.L Aviva"
    page.bgcolor      = BG
    page.theme_mode   = ft.ThemeMode.DARK
    page.window_width  = 420
    page.window_height = 820
    page.padding      = ft.Padding(0, 0, 0, 0)

    usr = {"id": None, "nome": None, "nivel": None}

    # ── FilePicker global — adicionado UMA VEZ e nunca removido do overlay ──
    foto_picker = ft.FilePicker()
    page.overlay.append(foto_picker)

    # ── helpers ───────────────────────────────────────

    def snack(msg, cor=VD):
        page.snack_bar = ft.SnackBar(content=ft.Text(msg, color="white"), bgcolor=cor)
        page.snack_bar.open = True
        page.update()

    def F(label, pw=False, w=None):
        return ft.TextField(
            label=label, password=pw, can_reveal_password=pw,
            color=TX, label_style=ft.TextStyle(color=SB),
            bgcolor=CARD, border_color=AC,
            focused_border_color=AC, cursor_color=AC,
            width=w, expand=w is None,
        )

    def B(label, fn, cor=AC, w=None):
        return ft.Container(
            content=ft.Text(label, color="white", weight=ft.FontWeight.BOLD,
                            text_align=ft.TextAlign.CENTER),
            bgcolor=cor, border_radius=10, on_click=fn,
            padding=ft.Padding(0, 14, 0, 14), alignment=ft.Alignment(0, 0),
            width=w, expand=w is None,
        )

    def badge(s):
        c = {"confirmado": VD, "recusado": VM, "pendente": AM}.get(s, AM)
        return ft.Container(
            ft.Text(s.capitalize(), size=11, color="white", weight=ft.FontWeight.BOLD),
            bgcolor=c, border_radius=20, padding=ft.Padding(6, 3, 6, 3),
        )

    def T(t, s=14, c=TX, b=False):
        return ft.Text(str(t), size=s, color=c,
                       weight=ft.FontWeight.BOLD if b else ft.FontWeight.NORMAL)

    def DIV(): return ft.Divider(color=C2, height=1)

    def is_min(): return usr["nivel"] == 1

    # ── overlay: remove apenas AlertDialogs, preserva o foto_picker ──────────

    def _fechar_dialogs():
        """Fecha e remove apenas AlertDialogs do overlay, preservando o foto_picker."""
        for ctrl in list(page.overlay):
            if isinstance(ctrl, ft.AlertDialog):
                ctrl.open = False
        page.overlay[:] = [c for c in page.overlay if not isinstance(c, ft.AlertDialog)]

    def dlg_abrir(dlg):
        _fechar_dialogs()
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def fechar(dlg):
        dlg.open = False
        _fechar_dialogs()
        page.update()

    # ── troca de tela ─────────────────────────────────

    def ir(controles, nav=True):
        _fechar_dialogs()
        page.controls.clear()
        page.scroll = None
        page.bgcolor = BG
        if nav:
            novas = db_contar_novas()
            dests = [
                ft.NavigationBarDestination(icon="home",          label="Início"),
                ft.NavigationBarDestination(icon="people",        label="Equipe"),
                ft.NavigationBarDestination(
                    icon="calendar_today",
                    label=f"Escala  •{novas}" if novas > 0 else "Escala",
                ),
                ft.NavigationBarDestination(icon="music_note",    label="Repertório"),
                ft.NavigationBarDestination(icon="event",         label="Agenda"),
            ]
            nav_bar.destinations = dests
            page.controls.append(ft.AppBar(
                title=ft.Text("M.L Aviva", color=TX, weight=ft.FontWeight.BOLD),
                bgcolor=CARD,
                actions=[ft.GestureDetector(
                    on_tap=lambda e: tela_login(),
                    content=ft.Container(
                        padding=8, bgcolor=CARD,
                        content=ft.Icon("logout", color=TX, size=22),
                    ),
                )],
            ))
        page.controls.append(
            ft.Column(
                controls=controles,
                tight=True,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            )
        )
        page.navigation_bar = nav_bar if nav else None
        page.update()

    # ── nav bar ───────────────────────────────────────

    nav_bar = ft.NavigationBar(
        bgcolor=CARD,
        indicator_color=AC,
        destinations=[
            ft.NavigationBarDestination(icon="home",          label="Início"),
            ft.NavigationBarDestination(icon="people",        label="Equipe"),
            ft.NavigationBarDestination(icon="calendar_today",label="Escala"),
            ft.NavigationBarDestination(icon="music_note",    label="Repertório"),
            ft.NavigationBarDestination(icon="event",         label="Agenda"),
        ],
    )
    telas = []

    def on_nav_change(e):
        idx = e.control.selected_index
        nav_bar.selected_index = idx
        telas[idx]()

    nav_bar.on_change = on_nav_change

    # ══════════════════════════════════════════════════
    #  LOGIN
    # ══════════════════════════════════════════════════

    def tela_login():
        _fechar_dialogs()
        page.navigation_bar = None
        page.scroll = None
        f_nome  = F("Nome")
        f_senha = F("Senha", pw=True)

        def entrar(e):
            nome  = (f_nome.value  or "").strip()
            senha = (f_senha.value or "").strip()
            if not nome:
                snack("Informe o nome de usuário.", VM); return
            if len(senha) < 8:
                snack("Senha muito curta!", VM); return
            try:
                r = db_login(nome, senha)
            except Exception as ex:
                snack(f"Erro de conexão: {ex}", VM); return
            if r:
                usr["id"] = r[0]; usr["nome"] = r[1]; usr["nivel"] = r[2]
                nav_bar.selected_index = 0
                tela_inicio()
            else:
                snack("Usuário ou senha incorretos!", VM)

        page.controls.clear()
        page.scroll = ft.ScrollMode.AUTO
        page.controls.append(ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            controls=[
                ft.Container(
                    height=280, bgcolor=BG,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=90, height=90,
                                bgcolor=AC, border_radius=45,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon("music_note", size=50, color="white"),
                            ),
                            ft.Container(height=4),
                            T("M.L Aviva", s=30, b=True),
                            T("Ministério de Louvor", s=14, c=SB),
                        ],
                    ),
                ),
                ft.Container(height=20),
                f_nome,
                ft.Container(height=8),
                f_senha,
                ft.Container(height=20),
                ft.Container(
                    content=ft.Text("  Entrar  ", color="white",
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                    size=16),
                    bgcolor=AC, border_radius=10, on_click=entrar,
                    padding=ft.Padding(0, 14, 0, 14),
                    alignment=ft.Alignment(0, 0),
                    width=320,
                ),
                ft.Container(height=8),
                ft.TextButton(
                    "Não tem conta? Cadastre-se",
                    on_click=lambda e: tela_cadastro(),
                    style=ft.ButtonStyle(color=AC),
                ),
                ft.Container(height=20),
            ],
        ))
        page.update()

    # ══════════════════════════════════════════════════
    #  CADASTRO
    # ══════════════════════════════════════════════════

    def tela_cadastro():
        _fechar_dialogs()
        page.navigation_bar = None
        f_nome  = F("Nome de usuário")
        f_senha = F("Senha (mín. 8 caracteres)", pw=True)
        f_conf  = F("Confirmar senha", pw=True)

        def cadastrar(e):
            nome = f_nome.value.strip()
            senha = f_senha.value.strip()
            conf  = f_conf.value.strip()
            if not nome:
                snack("Informe um nome de usuário", VM); return
            if senha != conf:
                snack("As senhas não coincidem!", VM); return
            r = db_cadastrar(nome, senha, nivel=0)
            if r == "ok":
                snack("✅ Cadastro realizado! Faça o login.")
                tela_login()
            else:
                snack(r, VM)

        page.controls.clear()
        page.scroll = ft.ScrollMode.AUTO
        page.controls.append(ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
            controls=[
                ft.Container(
                    height=200, bgcolor=BG,
                    alignment=ft.Alignment(0, 0),
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        alignment=ft.MainAxisAlignment.CENTER,
                        spacing=10,
                        controls=[
                            ft.Container(
                                width=70, height=70,
                                bgcolor=AC, border_radius=35,
                                alignment=ft.Alignment(0, 0),
                                content=ft.Icon("person_add", size=36, color="white"),
                            ),
                            ft.Container(height=4),
                            T("Criar conta", s=24, b=True),
                            T("M.L Aviva", s=13, c=SB),
                        ],
                    ),
                ),
                ft.Container(
                    width=320,
                    content=ft.Row([
                        ft.GestureDetector(
                            on_tap=lambda e: tela_login(),
                            content=ft.Container(
                                padding=8,
                                content=ft.Icon("arrow_back", color=TX, size=22),
                            ),
                        ),
                        T("Cadastro", s=20, b=True),
                    ]),
                ),
                ft.Container(height=12),
                f_nome,
                ft.Container(height=8),
                f_senha,
                ft.Container(height=8),
                f_conf,
                ft.Container(
                    padding=ft.Padding(0, 8, 0, 0),
                    width=320,
                    content=ft.Text(
                        "ℹ️  Cadastro público cria conta de Membro. "
                        "Ministros são promovidos pelo líder na tela Equipe.",
                        size=11, color=SB,
                    ),
                ),
                ft.Container(height=12),
                ft.Container(
                    content=ft.Text("  Cadastrar  ", color="white",
                                    weight=ft.FontWeight.BOLD,
                                    text_align=ft.TextAlign.CENTER,
                                    size=16),
                    bgcolor=AC, border_radius=10, on_click=cadastrar,
                    padding=ft.Padding(0, 14, 0, 14),
                    alignment=ft.Alignment(0, 0),
                    width=320,
                ),
                ft.Container(height=8),
                ft.TextButton(
                    "Já tem conta? Faça o login",
                    on_click=lambda e: tela_login(),
                    style=ft.ButtonStyle(color=AC),
                ),
                ft.Container(height=20),
            ],
        ))
        page.update()

    # ══════════════════════════════════════════════════
    #  INÍCIO
    # ══════════════════════════════════════════════════

    def tela_inicio():
        def nc(label, icon, idx):
            return ft.GestureDetector(
                on_tap=lambda e, i=idx: [
                    setattr(nav_bar, "selected_index", i),
                    telas[i](),
                ],
                content=ft.Container(
                    bgcolor=C2, border_radius=12, padding=14,
                    content=ft.Row([ft.Icon(icon, color=AC, size=20), T(label, s=14)], spacing=10),
                ),
            )

        ir([ft.Container(padding=20, content=ft.Column(spacing=16, controls=[
            ft.Container(
                padding=20, border_radius=16,
                gradient=ft.LinearGradient(
                    begin=ft.Alignment(-1, -1), end=ft.Alignment(1, 1),
                    colors=[AC, C2],
                ),
                content=ft.Column([
                    ft.Icon("music_note", color="white", size=44),
                    T("Ministério de Louvor Aviva", s=20, c="white", b=True),
                    ft.Divider(color="white24"),
                    T("Bem-vindo ao app do M.L Aviva!\n"
                      "Gerencie escalas, repertório e muito mais.", s=13, c="white70"),
                ], spacing=8),
            ),
            T(f"Olá, {usr['nome']} 👋", s=16),
            T("Ministro 🎤" if is_min() else "Membro 🎵", s=13, c=SB),
            DIV(),
            T("Navegação rápida", s=15, b=True),
            ft.Row(wrap=True, spacing=10, run_spacing=10, controls=[
                nc("Equipe",     "people",          1),
                nc("Escala",     "calendar_today",  2),
                nc("Repertório", "music_note",       3),
                nc("Agenda",     "event",            4),
            ]),
        ]))])

    # ══════════════════════════════════════════════════
    #  EQUIPE
    # ══════════════════════════════════════════════════

    def tela_equipe():
        lista = ft.Column(spacing=8)

        def on_foto_result(e: ft.FilePickerResultEvent, id_u):
            if e.files:
                caminho = e.files[0].path
                db_salvar_foto(id_u, caminho)
                snack("Foto atualizada! 📷")
                refresh()

        def abrir_picker(id_u):
            foto_picker.on_result = lambda e: on_foto_result(e, id_u)
            foto_picker.pick_files(allowed_extensions=["jpg", "jpeg", "png"])

        def refresh():
            lista.controls.clear()
            for id_u, nm, nv, fns, foto in db_membros():
                if foto and os.path.exists(foto):
                    avatar = ft.CircleAvatar(foreground_image_src=foto, radius=22)
                else:
                    avatar = ft.CircleAvatar(
                        content=ft.Text(nm[0].upper(), color="white"),
                        bgcolor=AC, radius=22,
                    )
                lista.controls.append(
                    ft.Container(bgcolor=C2, border_radius=12, padding=14,
                        content=ft.Row([
                            avatar,
                            ft.Column([
                                T(nm, b=True),
                                T(fns or "Sem função", s=12, c=SB),
                                T("Ministro 🎤" if nv == 1 else "Membro 🎵", s=11, c=AC),
                            ], expand=True, spacing=2),
                            ft.PopupMenuButton(
                                icon="more_vert", icon_color=SB,
                                visible=is_min() or id_u == usr["id"],
                                items=[
                                    ft.PopupMenuItem(
                                        text="Alterar foto",
                                        on_click=lambda e, u=id_u: abrir_picker(u),
                                    ),
                                    ft.PopupMenuItem(text="Atribuir função",
                                        on_click=lambda e, u=id_u: dlg_funcao(u, refresh),
                                        visible=is_min()),
                                    ft.PopupMenuItem(text="Remover membro",
                                        on_click=lambda e, u=id_u: dlg_rem_mb(u, refresh),
                                        visible=is_min()),
                                ],
                            ) if is_min() or id_u == usr["id"] else ft.Container(),
                        ]),
                    )
                )
            page.update()

        refresh()
        f_nm = F("Novo membro")
        f_pw = F("Senha", pw=True)
        dd_nv = ft.Dropdown(
            label="Nível", value="0", bgcolor=CARD, color=TX,
            border_color=AC, expand=True,
            options=[ft.dropdown.Option("0", "Membro"), ft.dropdown.Option("1", "Ministro")],
        )

        def add(e):
            if not is_min():
                snack("Sem permissão para esta ação.", VM); return
            r = db_cadastrar(f_nm.value.strip(), f_pw.value.strip(), int(dd_nv.value))
            if r == "ok":
                snack("Membro adicionado!")
                f_nm.value = ""; f_pw.value = ""
                refresh()
            else:
                snack(r, VM)

        ctrl = [ft.Container(padding=16, content=ft.Column(spacing=12, controls=[
            T("Equipe", s=22, b=True),
            T("Ministério de Louvor Aviva", s=13, c=SB),
            DIV(), lista,
        ]))]
        if is_min():
            ctrl[0].content.controls += [
                DIV(), T("Adicionar membro", s=14, b=True),
                f_nm, f_pw, dd_nv, B("Adicionar", add),
            ]
        ir(ctrl)

    def dlg_funcao(id_u, cb):
        fns = db_funcoes()
        dd = ft.Dropdown(
            label="Função existente", bgcolor=CARD, color=TX, border_color=AC,
            options=[ft.dropdown.Option(str(f[0]), f[1]) for f in fns],
        )
        f_nova = F("Ou crie nova função")

        def salvar(e):
            if dd.value:
                db_atribuir_funcao(id_u, int(dd.value))
            elif f_nova.value.strip():
                db_add_funcao(f_nova.value.strip())
                for f in db_funcoes():
                    if f[1] == f_nova.value.strip():
                        db_atribuir_funcao(id_u, f[0]); break
            fechar(dlg)
            cb()

        dlg = ft.AlertDialog(
            title=ft.Text("Atribuir Função", color=TX), bgcolor=CARD,
            content=ft.Column([dd, f_nova], tight=True, spacing=10),
            actions=[ft.TextButton("Salvar", on_click=salvar, style=ft.ButtonStyle(color=AC))],
        )
        dlg_abrir(dlg)

    def dlg_rem_mb(id_u, cb):
        def ok(e):
            db_remover_membro(id_u)
            fechar(dlg)
            cb()
        dlg = ft.AlertDialog(
            title=ft.Text("Remover membro?", color=TX), bgcolor=CARD,
            content=ft.Text("Esta ação não pode ser desfeita.", color=SB),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar(dlg), style=ft.ButtonStyle(color=SB)),
                ft.TextButton("Remover",  on_click=ok, style=ft.ButtonStyle(color=VM)),
            ],
        )
        dlg_abrir(dlg)

    # ══════════════════════════════════════════════════
    #  ESCALA
    # ══════════════════════════════════════════════════

    def tela_escala():
        lista = ft.Column(spacing=8)

        def refresh():
            lista.controls.clear()
            for id_e, dt, hr, nm, nova in db_escalas():
                conf, total = db_status_escala(id_e)
                lista.controls.append(ft.GestureDetector(
                    on_tap=lambda e, eid=id_e: dlg_escala(eid, refresh),
                    content=ft.Container(bgcolor=C2, border_radius=12, padding=14,
                        content=ft.Column([
                            ft.Row([
                                ft.Column([
                                    ft.Row([
                                        T(str(dt), b=True),
                                        ft.Container(
                                            ft.Text("NOVA", size=10, color="white",
                                                    weight=ft.FontWeight.BOLD),
                                            bgcolor=AC, border_radius=10,
                                            padding=ft.Padding(6, 3, 6, 3),
                                            visible=bool(nova),
                                        ),
                                    ], spacing=8),
                                    T(nm or "", s=12, c=SB),
                                    T(hr or "", s=12, c=SB),
                                ], expand=True, spacing=2),
                                ft.PopupMenuButton(
                                    icon="more_vert", icon_color=SB, visible=is_min(),
                                    items=[ft.PopupMenuItem(
                                        text="Excluir",
                                        on_click=lambda e, eid=id_e: dlg_del_escala(eid, refresh),
                                    )],
                                ) if is_min() else ft.Container(),
                            ]),
                            ft.ProgressBar(
                                value=conf / total if total else 0,
                                bgcolor=BG, color=VD, height=6,
                            ),
                            T(f"{conf} de {total} confirmados", s=11, c=SB),
                        ], spacing=6),
                    ),
                ))
            page.update()

        refresh()

        f_data = ft.TextField(
            label="Data (DD/MM/AAAA)", hint_text="ex: 25/12/2025",
            color=TX, label_style=ft.TextStyle(color=SB),
            bgcolor=CARD, border_color=AC,
            focused_border_color=AC, cursor_color=AC, expand=True,
            keyboard_type=ft.KeyboardType.NUMBER,
        )
        f_hr = F("Horário (ex: 19:00)")
        f_nm = F("Nome da escala (opcional)")

        def criar(e):
            raw = f_data.value.strip()
            if not raw:
                snack("Informe a data", VM); return
            try:
                dt_val = datetime.strptime(raw, "%d/%m/%Y").date()
            except ValueError:
                snack("Data inválida. Use DD/MM/AAAA", VM); return
            db_criar_escala(dt_val, f_hr.value.strip(), f_nm.value.strip())
            snack("Escala criada! 🎉")
            f_data.value = ""; f_hr.value = ""; f_nm.value = ""
            refresh()

        ctrl = [ft.Container(padding=16, content=ft.Column(spacing=12, controls=[
            T("Escalas", s=22, b=True), DIV(), lista,
        ]))]
        if is_min():
            ctrl[0].content.controls += [
                DIV(),
                T("Nova escala", s=14, b=True),
                f_data, f_hr, f_nm,
                B("Criar escala", criar),
            ]
        ir(ctrl)

    def dlg_del_escala(id_e, cb):
        def ok(e):
            db_deletar_escala(id_e)
            fechar(dlg)
            cb()
        dlg = ft.AlertDialog(
            title=ft.Text("Excluir escala?", color=TX), bgcolor=CARD,
            content=ft.Text("Esta ação não pode ser desfeita.", color=SB),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar(dlg), style=ft.ButtonStyle(color=SB)),
                ft.TextButton("Excluir",  on_click=ok, style=ft.ButtonStyle(color=VM)),
            ],
        )
        dlg_abrir(dlg)

    def dlg_escala(id_e, cb_ext=None):
        db_marcar_vista(id_e)
        todos = db_membros()
        fns   = db_funcoes()
        lista = ft.Column(spacing=8)

        def refresh():
            lista.controls.clear()
            for id_em, nm, func, status, justif, id_u in db_membros_escala(id_e):
                if usr["id"] is None:
                    tela_login(); return
                eh_eu = id_u == usr["id"]
                lista.controls.append(ft.Container(
                    bgcolor=BG, border_radius=10, padding=10,
                    content=ft.Column([
                        ft.Row([
                            ft.CircleAvatar(
                                content=ft.Text(nm[0].upper(), color="white"),
                                bgcolor=AC, radius=16,
                            ),
                            ft.Column([
                                T(nm, b=True),
                                T(func or "Sem função", s=12, c=SB),
                            ], expand=True, spacing=2),
                            badge(status),
                            ft.GestureDetector(
                                on_tap=lambda e, eid=id_em: [
                                    db_rem_membro_escala(eid),
                                    refresh(),
                                    cb_ext() if cb_ext else None,
                                ],
                                visible=is_min(),
                                content=ft.Container(
                                    padding=6,
                                    content=ft.Icon("remove_circle_outline", color=VM, size=22),
                                ),
                            ),
                        ]),
                        ft.Text(
                            f"Motivo: {justif}", color=VM, size=11,
                            visible=bool(justif and status == "recusado"),
                        ),
                        ft.Row([
                            B("✓ Confirmar",
                              lambda e, eid=id_em: [
                                  db_responder(eid, "confirmado"),
                                  refresh(),
                                  cb_ext() if cb_ext else None,
                              ],
                              cor=VD, w=140),
                            B("✗ Recusar",
                              lambda e, eid=id_em: dlg_recusar(eid, refresh, cb_ext),
                              cor=VM, w=140),
                        ], visible=eh_eu and status == "pendente", spacing=8),
                    ], spacing=6),
                ))
            page.update()

        refresh()

        dd_u = ft.Dropdown(
            label="Membro", bgcolor=CARD, color=TX, border_color=AC,
            options=[ft.dropdown.Option(str(m[0]), m[1]) for m in todos],
        )
        dd_f = ft.Dropdown(
            label="Função na escala", bgcolor=CARD, color=TX, border_color=AC,
            options=[ft.dropdown.Option(str(f[0]), f[1]) for f in fns],
        )

        def add(e):
            if dd_u.value:
                db_add_membro_escala(id_e, int(dd_u.value),
                                     int(dd_f.value) if dd_f.value else None)
                snack("Membro adicionado!")
                refresh()
                if cb_ext: cb_ext()

        conteudo = ft.Column(
            scroll=ft.ScrollMode.AUTO,
            controls=[
                lista,
                DIV() if is_min() else ft.Container(),
                T("Adicionar membro", s=13, b=True) if is_min() else ft.Container(),
                dd_u  if is_min() else ft.Container(),
                dd_f  if is_min() else ft.Container(),
                B("Adicionar", add) if is_min() else ft.Container(),
            ],
            spacing=10,
        )

        dlg = ft.AlertDialog(
            title=ft.Text("Detalhe da Escala", color=TX), bgcolor=CARD,
            content=ft.Container(content=conteudo, width=380, height=440),
            actions=[ft.TextButton("Fechar", on_click=lambda e: fechar(dlg),
                                   style=ft.ButtonStyle(color=SB))],
        )
        dlg_abrir(dlg)

    def dlg_recusar(id_em, cb, cb_ext=None):
        f_just = F("Motivo (obrigatório)")

        def ok(e):
            if not f_just.value.strip():
                snack("Informe o motivo", VM); return
            db_responder(id_em, "recusado", f_just.value.strip())
            fechar(dlg)
            cb()
            if cb_ext: cb_ext()

        dlg = ft.AlertDialog(
            title=ft.Text("Recusar escala", color=TX), bgcolor=CARD,
            content=f_just,
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar(dlg),
                              style=ft.ButtonStyle(color=SB)),
                ft.TextButton("Confirmar", on_click=ok,
                              style=ft.ButtonStyle(color=VM)),
            ],
        )
        dlg_abrir(dlg)

    # ══════════════════════════════════════════════════
    #  REPERTÓRIO
    # ══════════════════════════════════════════════════

    def tela_repertorio():
        escs  = db_escalas()
        lista = ft.Column(spacing=8)
        dd = ft.Dropdown(
            label="Filtrar por escala / data", value="0",
            bgcolor=CARD, color=TX, border_color=AC, expand=True,
            options=[ft.dropdown.Option("0", "Todas as músicas")] + [
                ft.dropdown.Option(
                    str(e[0]),
                    f"{e[1].strftime('%d/%m/%Y')}  {e[3] or ''}".strip(),
                )
                for e in escs
            ],
        )

        def refresh(e=None):
            lista.controls.clear()
            eid = int(dd.value) if dd.value else 0
            musicas = db_musicas_escala(eid) if eid else db_todas_musicas()

            if not musicas:
                lista.controls.append(T("Nenhuma música encontrada.", c=SB))
            for id_m, nm, tom, cifra, letra, video in musicas:
                lista.controls.append(ft.Container(
                    bgcolor=C2, border_radius=12, padding=14,
                    content=ft.Column([
                        ft.Row([
                            ft.Icon("music_note", color=AC, size=20),
                            ft.Column([
                                T(nm, b=True),
                                T(f"Tom: {tom or '—'}", s=12, c=SB),
                            ], expand=True, spacing=2),
                            ft.PopupMenuButton(
                                icon="more_vert", icon_color=SB, visible=is_min(),
                                items=[
                                    ft.PopupMenuItem(
                                        text="Remover da escala",
                                        on_click=lambda e, mid=id_m, e_=eid: [
                                            db_desvincular_musica(e_, mid), refresh()
                                        ],
                                        visible=eid > 0,
                                    ),
                                    ft.PopupMenuItem(
                                        text="Excluir música",
                                        on_click=lambda e, mid=id_m: dlg_del_musica(mid, refresh),
                                    ),
                                ],
                            ) if is_min() else ft.Container(),
                        ]),
                        ft.Row([
                            ft.TextButton("Cifra",  on_click=lambda e, u=cifra: page.launch_url(u),  visible=bool(cifra),
                                          style=ft.ButtonStyle(color=AC)),
                            ft.TextButton("Letra",  on_click=lambda e, u=letra: page.launch_url(u),  visible=bool(letra),
                                          style=ft.ButtonStyle(color=AC)),
                            ft.TextButton("Vídeo",  on_click=lambda e, u=video: page.launch_url(u),  visible=bool(video),
                                          style=ft.ButtonStyle(color=AC)),
                        ], spacing=4),
                    ], spacing=6),
                ))
            page.update()

        dd.on_change = refresh
        refresh()

        f_nm  = F("Nome da música")
        f_tom = F("Tom (ex: C, Am)")
        f_cif = F("Link da cifra")
        f_let = F("Link da letra")
        f_vid = F("Link do vídeo (YouTube)")
        dd2 = ft.Dropdown(
            label="Vincular à escala (opcional)", value="0",
            bgcolor=CARD, color=TX, border_color=AC, expand=True,
            options=[ft.dropdown.Option("0", "Nenhuma")] + [
                ft.dropdown.Option(
                    str(e[0]),
                    f"{e[1].strftime('%d/%m/%Y')}  {e[3] or ''}".strip(),
                )
                for e in escs
            ],
        )

        def add(e):
            if not f_nm.value.strip():
                snack("Informe o nome da música", VM); return
            mid = db_add_musica(
                f_nm.value.strip(), f_tom.value.strip(),
                f_cif.value.strip(), f_let.value.strip(), f_vid.value.strip(),
            )
            eid2 = int(dd2.value)
            if eid2: db_vincular_musica(eid2, mid)
            snack("Música adicionada! 🎵")
            for f in [f_nm, f_tom, f_cif, f_let, f_vid]: f.value = ""
            refresh()

        ctrl = [ft.Container(padding=16, content=ft.Column(spacing=12, controls=[
            T("Repertório", s=22, b=True), dd, DIV(), lista,
        ]))]
        if is_min():
            ctrl[0].content.controls += [
                DIV(), T("Adicionar música", s=14, b=True),
                f_nm, f_tom, f_cif, f_let, f_vid, dd2,
                B("Adicionar música", add),
            ]
        ir(ctrl)

    def dlg_del_musica(id_m, cb):
        def ok(e):
            db_deletar_musica(id_m)
            fechar(dlg)
            cb()
        dlg = ft.AlertDialog(
            title=ft.Text("Excluir música?", color=TX), bgcolor=CARD,
            content=ft.Text("Remove de todas as escalas.", color=SB),
            actions=[
                ft.TextButton("Cancelar", on_click=lambda e: fechar(dlg),
                              style=ft.ButtonStyle(color=SB)),
                ft.TextButton("Excluir",  on_click=ok,
                              style=ft.ButtonStyle(color=VM)),
            ],
        )
        dlg_abrir(dlg)

    # ══════════════════════════════════════════════════
    #  AGENDA
    # ══════════════════════════════════════════════════

    def tela_agenda():
        escs  = db_escalas()
        hoje  = date.today()
        MESES = ["", "Janeiro", "Fevereiro", "Março", "Abril", "Maio", "Junho",
                 "Julho", "Agosto", "Setembro", "Outubro", "Novembro", "Dezembro"]
        DIAS_SEMANA = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]

        esc_por_data: dict[date, list] = {}
        for id_e, dt, hr, nm, nova in escs:
            if isinstance(dt, str):
                dt = datetime.strptime(dt, "%Y-%m-%d").date()
            esc_por_data.setdefault(dt, []).append((id_e, hr, nm, nova))

        status_cache: dict[int, tuple] = {
            id_e: db_status_escala(id_e)
            for id_e, dt, hr, nm, nova in escs
        }

        meses_com_escala: set[tuple] = {(d.year, d.month) for d in esc_por_data}
        meses_com_escala.add((hoje.year, hoje.month))

        ag = ft.Column(spacing=24)

        for (ano, mes) in sorted(meses_com_escala):
            semana_cells = [
                ft.Container(
                    content=ft.Text(d, size=11, color=SB,
                                    text_align=ft.TextAlign.CENTER,
                                    weight=ft.FontWeight.BOLD),
                    width=48, height=28,
                    alignment=ft.Alignment(0, 0),
                )
                for d in DIAS_SEMANA
            ]

            primeiro_dia, total_dias = calendar.monthrange(ano, mes)
            cells = []
            for _ in range(primeiro_dia):
                cells.append(ft.Container(width=48, height=48))

            for dia in range(1, total_dias + 1):
                d = date(ano, mes, dia)
                escalas_do_dia = esc_por_data.get(d, [])
                tem_escala = bool(escalas_do_dia)
                eh_hoje    = d == hoje

                if eh_hoje and tem_escala:
                    bg = AC
                elif eh_hoje:
                    bg = "#2a2a4a"
                elif tem_escala:
                    if escalas_do_dia:
                        id_e0 = escalas_do_dia[0][0]
                        conf, total_m = status_cache.get(id_e0, (0, 0))
                        bg = "#1b4332" if (conf == total_m and total_m > 0) else C2
                    else:
                        bg = C2
                else:
                    bg = "transparent"

                tem_nova = any(e[3] for e in escalas_do_dia)

                cell_content = ft.Stack([
                    ft.Container(
                        width=48, height=48,
                        bgcolor=bg,
                        border_radius=10,
                        alignment=ft.Alignment(0, 0),
                        border=ft.border.all(1, AC) if eh_hoje else None,
                        content=ft.Column([
                            ft.Text(str(dia), size=14, color=TX if bg != "transparent" else SB,
                                    weight=ft.FontWeight.BOLD if tem_escala or eh_hoje else ft.FontWeight.NORMAL,
                                    text_align=ft.TextAlign.CENTER),
                            ft.Container(
                                width=6, height=6,
                                bgcolor=VD, border_radius=3,
                                visible=tem_escala,
                            ),
                        ], spacing=0,
                           alignment=ft.MainAxisAlignment.CENTER,
                           horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                    ),
                    ft.Container(
                        width=14, height=14,
                        bgcolor=AM, border_radius=7,
                        alignment=ft.Alignment(0, 0),
                        visible=tem_nova,
                        right=0, top=0,
                        content=ft.Text("!", size=9, color="white",
                                        weight=ft.FontWeight.BOLD,
                                        text_align=ft.TextAlign.CENTER),
                    ),
                ])

                def tap_factory(escalas, d_tap):
                    def on_tap(e):
                        if escalas:
                            if len(escalas) == 1:
                                dlg_escala(escalas[0][0])
                            else:
                                dlg_escolher_escala(escalas, d_tap)
                    return on_tap

                cells.append(ft.GestureDetector(
                    on_tap=tap_factory(escalas_do_dia, d),
                    content=cell_content,
                ) if tem_escala else cell_content)

            rows = []
            row_w = [ft.Row(semana_cells, spacing=4)]
            row_cur = []
            for i, cell in enumerate(cells):
                row_cur.append(cell)
                if len(row_cur) == 7:
                    rows.append(ft.Row(row_cur, spacing=4))
                    row_cur = []
            if row_cur:
                while len(row_cur) < 7:
                    row_cur.append(ft.Container(width=48, height=48))
                rows.append(ft.Row(row_cur, spacing=4))

            ag.controls.append(ft.Column([
                ft.Row([
                    ft.Icon("calendar_month", color=AC, size=16),
                    T(f"{MESES[mes]} {ano}", s=15, c=AC, b=True),
                ], spacing=6),
                *row_w,
                *rows,
            ], spacing=4))

            items_mes = sorted(
                [(d, escs_d) for d, escs_d in esc_por_data.items()
                 if d.year == ano and d.month == mes],
                key=lambda x: x[0],
            )
            for d_item, escs_list in items_mes:
                for id_e, hr, nm, nova in escs_list:
                    conf, total_m = status_cache.get(id_e, (0, 0))
                    ag.controls[-1].controls.append(
                        ft.GestureDetector(
                            on_tap=lambda e, eid=id_e: dlg_escala(eid),
                            content=ft.Container(
                                bgcolor=C2, border_radius=12, padding=12,
                                margin=ft.Margin(0, 4, 0, 0),
                                content=ft.Row([
                                    ft.Container(
                                        width=44, height=44, bgcolor=BG, border_radius=8,
                                        alignment=ft.Alignment(0, 0),
                                        content=ft.Column([
                                            T(str(d_item.day), s=16, b=True),
                                            T(MESES[d_item.month][:3], s=9, c=SB),
                                        ], spacing=0,
                                           alignment=ft.MainAxisAlignment.CENTER,
                                           horizontal_alignment=ft.CrossAxisAlignment.CENTER),
                                    ),
                                    ft.Column([
                                        ft.Row([
                                            T(nm or "Escala", b=True),
                                            ft.Container(
                                                ft.Text("NOVA", size=9, color="white",
                                                        weight=ft.FontWeight.BOLD),
                                                bgcolor=AC, border_radius=8,
                                                padding=ft.Padding(4, 2, 4, 2),
                                                visible=bool(nova),
                                            ),
                                        ], spacing=6),
                                        T(hr or "", s=12, c=SB),
                                        T(f"{conf}/{total_m} confirmados", s=11,
                                          c=VD if conf == total_m and total_m > 0 else SB),
                                    ], expand=True, spacing=2),
                                    ft.Icon("chevron_right", color=SB),
                                ], spacing=10),
                            ),
                        )
                    )

        if not esc_por_data:
            ag.controls.append(T("Nenhuma escala cadastrada.", c=SB))

        ir([ft.Container(padding=16, content=ft.Column(spacing=12, controls=[
            T("Agenda", s=22, b=True),
            T("Dias com escala destacados — toque para ver detalhes", s=12, c=SB),
            DIV(), ag,
        ]))])

    def dlg_escolher_escala(escalas, d):
        items = []
        for id_e, hr, nm, nova in escalas:
            items.append(ft.ListTile(
                title=ft.Text(nm or "Escala", color=TX),
                subtitle=ft.Text(hr or "", color=SB),
                on_click=lambda e, eid=id_e: dlg_escala(eid),
            ))
        dlg = ft.AlertDialog(
            title=ft.Text(f"Escalas em {d.strftime('%d/%m/%Y')}", color=TX),
            bgcolor=CARD,
            content=ft.Column(items, tight=True, spacing=4),
            actions=[ft.TextButton("Fechar", on_click=lambda e: fechar(dlg),
                                   style=ft.ButtonStyle(color=SB))],
        )
        dlg_abrir(dlg)

    # ── iniciar ───────────────────────────────────────
    telas.extend([tela_inicio, tela_equipe, tela_escala, tela_repertorio, tela_agenda])
    init_db()
    tela_login()


ft.app(target=main)
