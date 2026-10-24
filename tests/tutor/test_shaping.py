from src.tutor.shaping import SentenceGate, tidy_tail


def run(tokens, truncated):
    g = SentenceGate()
    out = "".join(g.feed(t) for t in tokens)
    return out + g.finish(truncated)


def test_whole_answer_passes_through_unchanged():
    toks = ["A process is ", "a running program. ", "It has its own memory", "."]
    assert run(toks, truncated=False) == "".join(toks)


def test_truncated_tail_is_dropped_at_the_last_sentence():
    toks = ["A process is a running program. ", "It has its own ", "memory and a program cou"]
    assert run(toks, truncated=True) == "A process is a running program. "


def test_nothing_is_released_mid_sentence():
    g = SentenceGate()
    assert g.feed("A process is a runn") == ""
    assert g.feed("ing program. Next") == "A process is a running program. "


def test_list_lines_flush_on_newline():
    out = run(["- one\n", "- two\n", "- thr"], truncated=True)
    assert out == "- one\n- two\n"


def test_clipped_single_sentence_beats_an_empty_answer():
    assert run(["A process is a running prog"], truncated=True).endswith("…")


def test_tidy_tail_cuts_to_a_whole_word():
    assert tidy_tail("It has its own memo") == "It has its own…"
    assert tidy_tail("Done.") == "Done."
    assert tidy_tail("") == ""


def test_unit_cap_stops_the_answer_after_n_sentences():
    g = SentenceGate(max_units=2)
    out = g.feed("One. Two. Three. Four.")
    assert out == "One. Two. " and g.full
    assert g.feed("Five. ") == "" and g.finish(False) == ""


def test_unit_cap_counts_list_lines():
    g = SentenceGate(max_units=3)
    out = g.feed("Steps:\n- a\n- b\n- c\n")
    assert out.count("\n") == 3 and g.full


def test_unit_cap_does_not_trigger_on_a_short_answer():
    g = SentenceGate(max_units=5)
    assert g.feed("One. Two. ") == "One. Two. " and not g.full
