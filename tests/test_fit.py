import pytest

from jobbot.fit import FLAGS, behavior_summary, fit_action, fit_risks
from jobbot.schema import Assessment, Behavior, Profile


@pytest.mark.parametrize("text,flag", [
    ("É proibido o uso de inteligência artificial neste teste.", "proibe_ia"),
    ("Responda sem ajuda de IA.", "proibe_ia"),
    ("NÃO UTILIZE ChatGPT ou similares", "proibe_ia"),
    ("Não é permitido usar IA para responder", "proibe_ia"),
    ("Tempo limite de 30 minutos", "cronometrado"),
    ("Você terá 20 minutos para concluir", "cronometrado"),
    ("O cronômetro começa ao abrir a página", "cronometrado"),
    ("Você só tem uma única tentativa", "tentativa_unica"),
    ("Não será possível refazer o teste", "tentativa_unica"),
    ("O teste só pode ser feito apenas uma vez", "tentativa_unica"),
    ("Sua câmera ficará ligada durante a prova", "vigiado"),
    ("Sessão monitorada por proctoring", "vigiado"),
    ("Usamos reconhecimento facial", "vigiado"),
])
def test_fit_risks_each_flag_with_accent_and_case_variants(text, flag):
    assert flag in fit_risks(text)


@pytest.mark.parametrize("text", [
    "Responda com sinceridade, não há respostas certas ou erradas.",
    "A mídia social da empresa é ativa e a diária é boa",  # 'ia' inside other words must not trigger
    "",
])
def test_fit_risks_clean_text_is_empty(text):
    assert fit_risks(text) == []


def test_fit_risks_multiple_flags_in_fixed_order_without_duplicates():
    text = "A câmera ficará ligada. Tempo limite de 10 minutos. Câmera obrigatória. Uma única tentativa. Sem ajuda de IA."
    assert fit_risks(text) == ["proibe_ia", "cronometrado", "tentativa_unica", "vigiado"] == list(FLAGS)


@pytest.mark.parametrize("mode,flags,action", [
    ("auto", [], "responder"), ("auto", ["proibe_ia", "cronometrado"], "responder"),
    ("auto", ["vigiado"], "deixar_para_pessoa"),
    ("perguntar", [], "perguntar"), ("perguntar", ["vigiado", "proibe_ia"], "deixar_para_pessoa"),
    ("pular", [], "pular"), ("pular", ["vigiado"], "deixar_para_pessoa"),
])
def test_fit_action_table(mode, flags, action):
    assert fit_action(mode, flags) == action


def test_behavior_summary_uses_latest_assessment_only():
    p = Profile(
        behavior=Behavior("Autonomia e foco", ["aprender", "impacto"], "especialista"),
        assessments=[
            Assessment("2026-09-01", {"interesses.social": 90}, "alta"),
            Assessment("2026-10-25", {"interesses.pratico": 80, "interesses.social": 20, "personalidade.abertura": 50}, "alta"),
        ])
    s = behavior_summary(p)
    assert s["ultimo_teste"] == "2026-10-25"
    assert s["dimensoes_altas"] == "interesses.pratico" and s["dimensoes_baixas"] == "interesses.social"
    assert (s["work_style"], s["motivators"], s["track"]) == ("Autonomia e foco", "aprender, impacto", "especialista")
    assert s["confiabilidade"] == "alta"


def test_behavior_summary_empty_when_no_data():
    assert set(behavior_summary(Profile()).values()) == {""}


def test_behavior_summary_flags_low_reliability():
    p = Profile(assessments=[Assessment("2026-10-25", {"valores.salario": 100}, "baixa", ["respostas_uniformes"])])
    s = behavior_summary(p)
    assert s["confiabilidade"] == "baixa" and s["dimensoes_altas"] == "valores.salario"


@pytest.mark.parametrize("text,flag", [
    ("Ative a webcam antes de começar", "vigiado"),
    ("Sua tela será gravada durante o teste", "vigiado"),
    ("Há monitoramento por webcam e fiscalização", "vigiado"),
    ("Proibido o uso de ferramentas de inteligência artificial", "proibe_ia"),
    ("Não consulte IA durante a prova", "proibe_ia"),
    ("Uso de IA não é permitido", "proibe_ia"),
    ("Não é permitida a consulta a IA", "proibe_ia"),
    ("Você não poderá voltar às questões anteriores", "tentativa_unica"),
    ("Você tem apenas uma chance", "tentativa_unica"),
    ("Só pode fazer uma vez", "tentativa_unica"),
    ("Não é possível refazer o teste", "tentativa_unica"),
    ("Este é um teste cronometrado", "cronometrado"),
    ("Você terá 1 hora para responder", "cronometrado"),
    ("Responda em até 40 min", "cronometrado"),
])
def test_fit_risks_more_portuguese_phrasings(text, flag):
    assert flag in fit_risks(text)


@pytest.mark.parametrize("text", [
    "Tempo estimado: 15 minutos",
    "O formulário leva 5 minutos, sem pressa.",
    "Em média, 10 minutos para concluir o cadastro.",
])
def test_fit_risks_duration_estimates_are_not_a_time_limit(text):
    assert "cronometrado" not in fit_risks(text)
