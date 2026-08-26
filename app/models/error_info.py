"""Modelo de informação de erro amigável."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ErrorInfo:
    amigavel: str  # mensagem amigável para o usuário
    dica: str  # sugestão de ação
    icone: str  # ícone/emoji
    tecnico: str  # mensagem técnica original (log)
    nome: str  # nome do padrão detectado (ou 'generico')

    def to_dict(self) -> dict:
        return {
            "amigavel": self.amigavel,
            "dica": self.dica,
            "icone": self.icone,
            "tecnico": self.tecnico,
            "nome": self.nome,
        }

    @classmethod
    def from_dict(cls, data: dict) -> ErrorInfo:
        return cls(
            amigavel=data.get("amigavel", ""),
            dica=data.get("dica", ""),
            icone=data.get("icone", ""),
            tecnico=data.get("tecnico", ""),
            nome=data.get("nome", "generico"),
        )
