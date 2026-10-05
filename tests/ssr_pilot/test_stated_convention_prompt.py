# Unit tests for stated convention prompt rendering
from research.ssr_pilot.worlds import load_worlds
from research.ssr_pilot.bank import load_bank
from research.ssr_pilot.render import render_variant, VARIANTS, reference_text

def test_stated_convention_presence_and_no_leakage():
    worlds = load_worlds()
    assert len(worlds) == 24
    
    for w in worlds:
        bank = load_bank(w)
        ref_trace = bank["reference"]
        
        for v in VARIANTS:
            r_plain = render_variant(w, v, stated_convention=False)
            r_stated = render_variant(w, v, stated_convention=True)
            
            # 1. Prompt SHA differed
            assert r_plain["prompt_sha256"] != r_stated["prompt_sha256"]
            
            # 2. Stated convention text is present in prompt
            assert "Convention for tie-breaking:" in r_stated["prompt"]
            assert "Convention for tie-breaking:" not in r_plain["prompt"]
            
            # 3. Canonical reference text string (formatted answer) is NOT exposed as an explicit answer trace
            ref_str = reference_text(w, ref_trace, r_stated)
            # Ensure "TRACE: <ref_str>" is not in prompt
            assert f"TRACE: {ref_str}" not in r_stated["prompt"]
            
            # 4. Correct entity mapping retained
            assert r_stated["c2s"] == r_plain["c2s"]

if __name__ == "__main__":
    test_stated_convention_presence_and_no_leakage()
    print("All stated convention prompt tests passed!")
