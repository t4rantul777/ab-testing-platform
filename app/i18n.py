"""Internationalisation (i18n) for the Streamlit app.

A single translation dictionary keyed by string id, with English and Russian
values, plus a sidebar language selector. Pages call ``t("key")`` for every
user-facing string; logic never branches on translated text (labels are
decoupled from values via ``format_func`` / index comparisons).

Add a language by extending ``LANGUAGES`` and adding the code to each entry.
"""

from __future__ import annotations

import streamlit as st

# display label -> language code
LANGUAGES = {"English": "en", "Русский": "ru"}
_DEFAULT = "en"


def language_selector() -> str:
    """Render the language picker in the sidebar and return the active code.

    Call this once near the top of every page (after ``set_page_config``) before
    any ``t()`` call. The widget key is shared across pages so the choice
    persists as the user navigates the multipage app.
    """
    labels = list(LANGUAGES.keys())
    choice = st.sidebar.selectbox("🌐 Language · Язык", labels, key="lang_widget")
    st.session_state["_lang"] = LANGUAGES[choice]
    return st.session_state["_lang"]


def get_lang() -> str:
    return st.session_state.get("_lang", _DEFAULT)


def t(key: str, **kwargs) -> str:
    """Translate ``key`` into the active language, formatting with kwargs."""
    entry = TR.get(key)
    if entry is None:
        return key  # surface the missing key rather than crashing
    text = entry.get(get_lang()) or entry.get("en") or key
    if kwargs:
        text = text.format(**kwargs)
    return text


# ---------------------------------------------------------------------------
# Translation table
# ---------------------------------------------------------------------------
TR: dict[str, dict[str, str]] = {
    # ---- shared -----------------------------------------------------------
    "yes": {"en": "✅ yes", "ru": "✅ да"},
    "no": {"en": "❌ no", "ru": "❌ нет"},
    "significant_q": {"en": "Significant?", "ru": "Значимо?"},
    "p_value": {"en": "p-value", "ru": "p-value"},
    "alpha": {"en": "Significance level α", "ru": "Уровень значимости α"},
    "control": {"en": "Control", "ru": "Контроль"},
    "treatment": {"en": "Treatment", "ru": "Тест"},
    "metric_binary": {"en": "Binary (conversion)", "ru": "Бинарная (конверсия)"},
    "metric_continuous": {"en": "Continuous (revenue)", "ru": "Непрерывная (выручка)"},

    # ---- home -------------------------------------------------------------
    "home_title": {
        "en": "🧪 A/B Testing Statistical Significance Platform",
        "ru": "🧪 Платформа расчёта статзначимости A/B-тестов",
    },
    "home_caption": {
        "en": "Simulate experiments, test significance, and stop tests early "
              "without inflating the type-I error rate.",
        "ru": "Симулируй эксперименты, считай значимость и останавливай тесты "
              "раньше срока, не раздувая ошибку I рода.",
    },
    "home_body": {
        "en": (
            "This platform goes beyond a single t-test. It is a small but "
            "complete experimentation toolkit:\n\n"
            "- **🧪 Simulator** — generate binary or continuous experiments with "
            "a *known* ground-truth effect, so every method can be validated.\n"
            "- **📊 Significance** — Welch's t-test, two-proportion z-test, "
            "chi-square, with confidence intervals and effect sizes.\n"
            "- **⏱️ Sequential** — peek at your experiment as often as you like: "
            "SPRT, always-valid confidence sequences (mSPRT), and Pocock / "
            "O'Brien-Fleming group-sequential boundaries.\n"
            "- **⚡ Power & MDE** — sample-size planning, power curves and the "
            "minimum detectable effect.\n"
            "- **🗂️ History** — every run is logged to a local SQLite database.\n\n"
            "Use the sidebar to navigate. A good first step is the **Simulator**: "
            "create an experiment, then carry it into the other pages."
        ),
        "ru": (
            "Это не просто один t-тест, а небольшой, но полноценный инструмент "
            "для экспериментов:\n\n"
            "- **🧪 Симулятор** — генерируй бинарные или непрерывные эксперименты "
            "с *известным* истинным эффектом, чтобы проверять каждый метод.\n"
            "- **📊 Значимость** — t-тест Уэлча, z-тест двух долей, χ², с "
            "доверительными интервалами и размерами эффекта.\n"
            "- **⏱️ Последовательные** — подглядывай в эксперимент сколько "
            "угодно: SPRT, always-valid доверительные последовательности (mSPRT) "
            "и групповые границы Pocock / O'Brien-Fleming.\n"
            "- **⚡ Мощность и MDE** — планирование выборки, кривые мощности и "
            "минимальный детектируемый эффект.\n"
            "- **🗂️ История** — каждый запуск логируется в локальную базу SQLite.\n\n"
            "Навигация — слева. Начни с **Симулятора**: создай эксперимент и "
            "перенеси его на остальные страницы."
        ),
    },
    "home_m_tests": {"en": "Statistical tests", "ru": "Статистические тесты"},
    "home_m_tests_help": {"en": "t-test, z-test, chi-square, sequential",
                          "ru": "t-тест, z-тест, χ², последовательные"},
    "home_m_seq": {"en": "Sequential methods", "ru": "Последовательные методы"},
    "home_m_seq_help": {"en": "SPRT, mSPRT, group-sequential",
                        "ru": "SPRT, mSPRT, групповые границы"},
    "home_m_ext": {"en": "External services required", "ru": "Внешних сервисов нужно"},
    "home_m_ext_help": {"en": "Fully self-contained", "ru": "Полностью автономно"},
    "home_sub_why": {"en": "Why sequential testing matters",
                     "ru": "Почему последовательное тестирование важно"},
    "home_why_body": {
        "en": "If you run a classic fixed-horizon test but check the p-value "
              "every day and stop the moment it dips below 0.05, your real "
              "false-positive rate is **not 5%** — with five looks it is about "
              "**14%**, and it keeps climbing with every peek. The Sequential "
              "page shows the boundaries that fix this, and lets you watch an "
              "always-valid confidence interval tighten in real time.",
        "ru": "Если запустить обычный тест с фиксированным горизонтом, но "
              "проверять p-value каждый день и останавливаться, как только он "
              "упадёт ниже 0.05, реальная вероятность ложного срабатывания будет "
              "**не 5%** — при пяти взглядах это около **14%**, и она растёт с "
              "каждым подглядыванием. Страница «Последовательные» показывает "
              "границы, которые это чинят, и как доверительный интервал сужается "
              "в реальном времени.",
    },
    "home_info": {
        "en": "Everything here runs locally on simulated data — no API keys, no "
              "database server, no cloud. Open the **Sequential** page to see "
              "the headline feature.",
        "ru": "Всё работает локально на симулированных данных — без API-ключей, "
              "без сервера БД, без облака. Открой страницу **Последовательные**, "
              "чтобы увидеть ключевую фишку.",
    },

    # ---- simulator --------------------------------------------------------
    "sim_title": {"en": "🧪 Experiment Simulator", "ru": "🧪 Симулятор экспериментов"},
    "sim_caption": {
        "en": "Generate data with a known effect so every downstream method can "
              "be checked.",
        "ru": "Генерируем данные с известным эффектом, чтобы проверить каждый "
              "последующий метод.",
    },
    "sim_design": {"en": "Design", "ru": "Дизайн"},
    "sim_name": {"en": "Experiment name", "ru": "Название эксперимента"},
    "sim_metric_type": {"en": "Metric type", "ru": "Тип метрики"},
    "sim_baseline_rate": {"en": "Baseline conversion rate", "ru": "Базовая конверсия"},
    "sim_effect_as": {"en": "Effect as", "ru": "Эффект как"},
    "sim_effect_abs": {"en": "Absolute (pp)", "ru": "Абсолютный (пп)"},
    "sim_effect_rel": {"en": "Relative (%)", "ru": "Относительный (%)"},
    "sim_abs_lift": {"en": "Absolute lift (pp)", "ru": "Абсолютный прирост (пп)"},
    "sim_rel_lift": {"en": "Relative lift", "ru": "Относительный прирост"},
    "sim_control_mean": {"en": "Control mean", "ru": "Среднее контроля"},
    "sim_abs_mean_lift": {"en": "Absolute mean lift", "ru": "Прирост среднего (абс.)"},
    "sim_sigma": {"en": "Std. deviation (shared)", "ru": "Стд. отклонение (общее)"},
    "sim_users": {"en": "Users per arm", "ru": "Пользователей на группу"},
    "sim_seed": {"en": "Random seed", "ru": "Seed генератора"},
    "sim_sub_truth": {"en": "Ground truth vs observed", "ru": "Истина против наблюдаемого"},
    "sim_true_effect": {"en": "True effect", "ru": "Истинный эффект"},
    "sim_obs_effect": {"en": "Observed effect", "ru": "Наблюдаемый эффект"},
    "sim_control_obs": {"en": "Control (obs.)", "ru": "Контроль (набл.)"},
    "sim_treatment_obs": {"en": "Treatment (obs.)", "ru": "Тест (набл.)"},
    "sim_sub_dist": {"en": "Distribution by arm", "ru": "Распределение по группам"},
    "sim_conv_rate": {"en": "Conversion rate", "ru": "Конверсия"},
    "sim_metric_value": {"en": "Metric value", "ru": "Значение метрики"},
    "sim_sub_result": {"en": "Primary test result", "ru": "Результат основного теста"},
    "sim_effect_est": {"en": "Effect estimate", "ru": "Оценка эффекта"},
    "sim_ci_effect": {"en": "95% CI on the effect: [{lo}, {hi}]",
                      "ru": "95% ДИ на эффект: [{lo}, {hi}]"},
    "sim_save_btn": {"en": "💾 Save this experiment to history",
                     "ru": "💾 Сохранить эксперимент в историю"},
    "sim_saved": {"en": "Saved experiment #{eid} to the local database.",
                  "ru": "Эксперимент #{eid} сохранён в локальную базу."},
    "sim_next": {"en": "Now open **Sequential** or **Power & MDE** — they reuse "
                       "this experiment.",
                 "ru": "Теперь открой **Последовательные** или **Мощность и MDE** "
                       "— они переиспользуют этот эксперимент."},

    # ---- significance -----------------------------------------------------
    "sig_title": {"en": "📊 Significance Calculator", "ru": "📊 Калькулятор значимости"},
    "sig_caption": {
        "en": "The classic fixed-horizon analysis you run once, at the planned "
              "sample size.",
        "ru": "Классический анализ с фиксированным горизонтом — запускается один "
              "раз, на запланированном размере выборки.",
    },
    "sig_alt": {"en": "Alternative hypothesis", "ru": "Альтернативная гипотеза"},
    "sig_alt_two": {"en": "two-sided", "ru": "двусторонняя"},
    "sig_alt_larger": {"en": "larger", "ru": "больше"},
    "sig_alt_smaller": {"en": "smaller", "ru": "меньше"},
    "sig_input": {"en": "Input", "ru": "Источник данных"},
    "sig_input_sim": {"en": "Use simulated experiment", "ru": "Из симулятора"},
    "sig_input_manual": {"en": "Enter summary numbers", "ru": "Ввести числа вручную"},
    "sig_no_exp": {"en": "No experiment in memory yet — open the **Simulator** "
                         "page first.",
                   "ru": "В памяти пока нет эксперимента — сначала открой "
                         "**Симулятор**."},
    "sig_using": {"en": "Using **{name}** — {metric}, {n} users/arm.",
                  "ru": "Использую **{name}** — {metric}, {n} набл./группа."},
    "sig_metric": {"en": "Metric", "ru": "Метрика"},
    "sig_binary": {"en": "Binary", "ru": "Бинарная"},
    "sig_continuous": {"en": "Continuous", "ru": "Непрерывная"},
    "sig_control_users": {"en": "Control users", "ru": "Пользователи контроля"},
    "sig_control_conv": {"en": "Control conversions", "ru": "Конверсии контроля"},
    "sig_treat_users": {"en": "Treatment users", "ru": "Пользователи теста"},
    "sig_treat_conv": {"en": "Treatment conversions", "ru": "Конверсии теста"},
    "sig_cont_info": {"en": "For continuous input from summary stats, use the "
                            "Simulator page (raw samples are needed for a t-test).",
                      "ru": "Для непрерывной метрики из сводных чисел используй "
                            "Симулятор (для t-теста нужны сырые наблюдения)."},
    "sig_sub_ztest": {"en": "Two-proportion z-test", "ru": "z-тест двух долей"},
    "sig_control_rate": {"en": "Control rate", "ru": "Конверсия контроля"},
    "sig_treat_rate": {"en": "Treatment rate", "ru": "Конверсия теста"},
    "sig_abs_lift": {"en": "Absolute lift", "ru": "Абсолютный прирост"},
    "sig_rel_lift": {"en": "Relative lift", "ru": "Относительный прирост"},
    "sig_zstat": {"en": "z-statistic", "ru": "z-статистика"},
    "sig_ci_h": {"en": "95% CI on the lift: [{lo}, {hi}] · Cohen's h = {h}",
                 "ru": "95% ДИ на прирост: [{lo}, {hi}] · Cohen's h = {h}"},
    "sig_effect_ci_name": {"en": "Effect ± 95% CI", "ru": "Эффект ± 95% ДИ"},
    "sig_diff_axis": {"en": "Difference in conversion rate", "ru": "Разница в конверсии"},
    "sig_chi_exp": {"en": "Chi-square test (equivalent to the two-sided z-test)",
                    "ru": "χ²-тест (эквивалентен двустороннему z-тесту)"},
    "sig_chi_line": {"en": "χ² = {chi}, dof = {dof}, p = {p}",
                     "ru": "χ² = {chi}, dof = {dof}, p = {p}"},
    "sig_chi_note": {"en": "Without a continuity correction, χ² equals z² exactly "
                           "— a useful cross-check that the implementation is correct.",
                     "ru": "Без поправки на непрерывность χ² в точности равен z² — "
                           "удобная перекрёстная проверка корректности."},
    "sig_sub_ttest": {"en": "Welch's t-test (unequal variances)",
                      "ru": "t-тест Уэлча (неравные дисперсии)"},
    "sig_mean_diff": {"en": "Mean difference", "ru": "Разница средних"},
    "sig_tstat": {"en": "t-statistic", "ru": "t-статистика"},
    "sig_ci_d": {"en": "95% CI: [{lo}, {hi}] · df = {df} · Cohen's d = {d}",
                 "ru": "95% ДИ: [{lo}, {hi}] · df = {df} · Cohen's d = {d}"},

    # ---- sequential -------------------------------------------------------
    "seq_title": {"en": "⏱️ Sequential & Always-Valid Testing",
                  "ru": "⏱️ Последовательные и always-valid тесты"},
    "seq_caption": {"en": "Look at your experiment as often as you like — without "
                          "inflating the error rate.",
                    "ru": "Смотри на эксперимент сколько угодно раз — не раздувая "
                          "вероятность ошибки."},
    "seq_tab_group": {"en": "Group-sequential boundaries", "ru": "Групповые границы"},
    "seq_tab_av": {"en": "Always-valid (mSPRT)", "ru": "Always-valid (mSPRT)"},
    "seq_tab_sprt": {"en": "Wald SPRT", "ru": "SPRT Вальда"},
    "seq_group_md": {"en": "Pre-plan **K** interim looks. The boundaries below "
                           "keep the overall false-positive rate at α even though "
                           "you test K times.",
                     "ru": "Заранее планируем **K** промежуточных взглядов. "
                           "Границы ниже удерживают общую вероятность ложного "
                           "срабатывания на α, хотя ты тестируешь K раз."},
    "seq_K": {"en": "Number of looks (K)", "ru": "Число взглядов (K)"},
    "seq_shape": {"en": "Spending shape", "ru": "Форма расходования α"},
    "seq_naive196": {"en": "naive 1.96", "ru": "наивный 1.96"},
    "seq_look_axis": {"en": "Interim look", "ru": "Промежуточный взгляд"},
    "seq_bound_axis": {"en": "Rejection boundary (Z)", "ru": "Граница отклонения (Z)"},
    "seq_bound_name": {"en": "Boundary (Z)", "ru": "Граница (Z)"},
    "seq_spent": {"en": "Family-wise error actually spent",
                  "ru": "Фактически потраченная ошибка (FWER)"},
    "seq_spent_help": {"en": "Should match the target α — verified by the AGS "
                             "recursion.",
                       "ru": "Должна совпадать с целевой α — проверяется рекурсией "
                             "Armitage-McPherson-Rowe."},
    "seq_naive_metric": {"en": "If you naively used 1.96 at every look",
                         "ru": "Если наивно брать 1.96 на каждом взгляде"},
    "seq_over_target": {"en": "{d} over target", "ru": "{d} сверх нормы"},
    "seq_col_look": {"en": "Look", "ru": "Взгляд"},
    "seq_col_bound": {"en": "Z boundary", "ru": "Граница Z"},
    "seq_col_nominal": {"en": "Nominal p at this look", "ru": "Номинальный p на взгляде"},
    "seq_av_md": {"en": "The **always-valid** confidence sequence can be checked "
                        "at every observation. Stop as soon as the band clears "
                        "zero — the guarantee holds no matter when you stop.",
                  "ru": "**Always-valid** доверительную последовательность можно "
                        "проверять на каждом наблюдении. Останавливайся, как только "
                        "полоса уходит от нуля — гарантия держится при любой "
                        "остановке."},
    "seq_av_baseline": {"en": "Baseline rate", "ru": "Базовая конверсия"},
    "seq_av_lift": {"en": "True absolute lift", "ru": "Истинный абс. прирост"},
    "seq_av_maxusers": {"en": "Max users per arm", "ru": "Макс. пользователей на группу"},
    "seq_av_ciname": {"en": "95% confidence sequence", "ru": "95% доверит. последовательность"},
    "seq_av_effname": {"en": "Effect estimate", "ru": "Оценка эффекта"},
    "seq_av_true": {"en": "true effect", "ru": "истинный эффект"},
    "seq_av_stop": {"en": "stop @ {n}", "ru": "стоп @ {n}"},
    "seq_av_totobs": {"en": "Total observations", "ru": "Всего наблюдений"},
    "seq_av_diffaxis": {"en": "Treatment − control rate", "ru": "Тест − контроль (доля)"},
    "seq_av_success": {"en": "Significant after **{n}** observations — about "
                             "**{pct}%** fewer than running the full {total}.",
                       "ru": "Значимо после **{n}** наблюдений — примерно на "
                             "**{pct}%** меньше, чем полные {total}."},
    "seq_av_fail": {"en": "Did not reach significance within the simulated horizon.",
                    "ru": "Не достигло значимости в пределах симулированного горизонта."},
    "seq_sprt_md": {"en": "Wald's SPRT accumulates the log-likelihood ratio of H1 "
                          "vs H0 and stops when it crosses either boundary — accept "
                          "H0, reject H0, or keep going.",
                    "ru": "SPRT Вальда накапливает логарифм отношения правдоподобия "
                          "H1 против H0 и останавливается при пересечении границы — "
                          "принять H0, отвергнуть H0 или продолжать."},
    "seq_sprt_mu1": {"en": "H1 mean effect", "ru": "Средний эффект при H1"},
    "seq_sprt_truemu": {"en": "True mean (data)", "ru": "Истинное среднее (данные)"},
    "seq_sprt_len": {"en": "Stream length", "ru": "Длина потока"},
    "seq_sprt_llr": {"en": "cumulative log-LR", "ru": "накопленный log-LR"},
    "seq_sprt_reject": {"en": "reject H0", "ru": "отвергнуть H0"},
    "seq_sprt_accept": {"en": "accept H0", "ru": "принять H0"},
    "seq_sprt_obs_axis": {"en": "Observation", "ru": "Наблюдение"},
    "seq_sprt_llr_axis": {"en": "Cumulative log-likelihood ratio",
                          "ru": "Накопленный логарифм отношения правдоподобия"},
    "seq_sprt_v_reject": {"en": "✅ Reject H0 (effect detected)",
                          "ru": "✅ Отвергнуть H0 (эффект обнаружен)"},
    "seq_sprt_v_accept": {"en": "❌ Accept H0 (no effect)",
                          "ru": "❌ Принять H0 (эффекта нет)"},
    "seq_sprt_v_cont": {"en": "… inconclusive within the stream",
                        "ru": "… неопределённо в пределах потока"},
    "seq_sprt_decision": {"en": "Decision", "ru": "Решение"},
    "seq_sprt_after": {"en": "after {n} obs", "ru": "после {n} набл."},

    # ---- power ------------------------------------------------------------
    "pow_title": {"en": "⚡ Power & Minimum Detectable Effect",
                  "ru": "⚡ Мощность и минимальный детектируемый эффект"},
    "pow_caption": {"en": "Plan the experiment: how many users, how much power, "
                          "what is detectable.",
                    "ru": "Планируем эксперимент: сколько пользователей, какая "
                          "мощность, что вообще детектируемо."},
    "pow_metric": {"en": "Metric", "ru": "Метрика"},
    "pow_binary": {"en": "Binary", "ru": "Бинарная"},
    "pow_continuous": {"en": "Continuous", "ru": "Непрерывная"},
    "pow_target": {"en": "Target power", "ru": "Целевая мощность"},
    "pow_baseline": {"en": "Baseline rate", "ru": "Базовая конверсия"},
    "pow_mde_pp": {"en": "Effect to detect (pp)", "ru": "Эффект для детекции (пп)"},
    "pow_mean_diff": {"en": "Mean difference to detect", "ru": "Разница средних для детекции"},
    "pow_sigma": {"en": "Std. deviation", "ru": "Стд. отклонение"},
    "pow_sub_summary": {"en": "Design summary", "ru": "Сводка по дизайну"},
    "pow_users_arm": {"en": "Users per arm", "ru": "Пользователей на группу"},
    "pow_power_at_n": {"en": "Power at that n", "ru": "Мощность при этом n"},
    "pow_total_users": {"en": "Total users", "ru": "Всего пользователей"},
    "pow_vs_n": {"en": "**Power vs sample size** (fixed effect)",
                 "ru": "**Мощность от размера выборки** (эффект фиксирован)"},
    "pow_vs_effect": {"en": "**Power vs true effect** (fixed n)",
                      "ru": "**Мощность от истинного эффекта** (n фиксирован)"},
    "pow_pct_power": {"en": "{pct}% power", "ru": "{pct}% мощности"},
    "pow_power_axis": {"en": "Power", "ru": "Мощность"},
    "pow_true_effect_axis": {"en": "True effect size", "ru": "Истинный размер эффекта"},
    "pow_info": {"en": "With **{n}** users per arm at α={alpha} and {pct}% power, "
                       "the smallest reliably detectable effect is **{mde}**.",
                 "ru": "При **{n}** пользователях на группу, α={alpha} и {pct}% "
                       "мощности минимальный надёжно детектируемый эффект — **{mde}**."},

    # ---- history ----------------------------------------------------------
    "hist_title": {"en": "🗂️ Experiment History", "ru": "🗂️ История экспериментов"},
    "hist_caption": {"en": "Every saved run is stored in a local SQLite database "
                           "(real SQL, no server).",
                     "ru": "Каждый сохранённый запуск лежит в локальной базе SQLite "
                           "(настоящий SQL, без сервера)."},
    "hist_empty": {"en": "No experiments saved yet. Open the **Simulator** and "
                         "click *Save this experiment to history*.",
                   "ru": "Пока ничего не сохранено. Открой **Симулятор** и нажми "
                         "*Сохранить эксперимент в историю*."},
    "hist_c_id": {"en": "ID", "ru": "ID"},
    "hist_c_name": {"en": "Experiment", "ru": "Эксперимент"},
    "hist_c_metric": {"en": "Metric", "ru": "Метрика"},
    "hist_c_baseline": {"en": "Baseline", "ru": "База"},
    "hist_c_effect": {"en": "True effect", "ru": "Истинный эффект"},
    "hist_c_narm": {"en": "n/arm", "ru": "n/группа"},
    "hist_c_test": {"en": "Last test", "ru": "Последний тест"},
    "hist_c_p": {"en": "p-value", "ru": "p-value"},
    "hist_c_verdict": {"en": "Verdict", "ru": "Вердикт"},
    "hist_c_saved": {"en": "Saved at", "ru": "Сохранено"},
    "hist_v_sig": {"en": "✅ significant", "ru": "✅ значимо"},
    "hist_v_nsig": {"en": "❌ not sig.", "ru": "❌ не значимо"},
    "hist_v_none": {"en": "—", "ru": "—"},
    "hist_logged": {"en": "Experiments logged", "ru": "Экспериментов в базе"},
    "hist_sub_sql": {"en": "Underlying SQL", "ru": "Лежащий в основе SQL"},
}
