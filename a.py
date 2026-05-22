import flet as ft

def main(page: ft.Page):
    page.title = "LouvePiratãoOfCrias"
    page.add(ft.Text("Escolha o que deseja."),
    ft.ElevatedButton("👥 Equipe", on_click=lambda e: equipe()),
    ft.ElevatedButton("📅 Escala", on_click=lambda e: escala()),
    ft.ElevatedButton("🎵 Repertório", onclick=lambda e: repertorio()),
    ft.ElevatedButton("📆 Agenda", onclick=lambda e: agenda())
    )

    def equipe():
      page.title = "Equipe"
      page.clean()
      page.add(
      ft.Text("Equipe", size=30)
      )  
    def escala(page: ft.Page):
      
      page.title = "Escala"
      page.clean()
      page.add(
      ft.Text("Escala", size=30)
      )  
    def repertorio(page: ft.Page):
      page.title = "Repertório"
      page.clean()
      page.add(
      ft.Text("Repertório", size=30)
      )  
    def agenda(page: ft.Page):
      page.title = "Agenda"
      page.clean()
      page.add(
      ft.Text("Agenda", size=30)
      )  

ft.app(target=main)