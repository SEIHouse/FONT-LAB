"""Fractional Display weights must retain every Boolean input and existing output."""
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import pathops
from font_builder import FontBuilderCore
from display.outline_cleanup import display_union
from verify_display_shapes import flags
from types import SimpleNamespace

ROOT=Path(__file__).resolve().parents[1]


class MotionUnionTests(unittest.TestCase):
    def test_final_cff_rounding_debris_is_repaired_without_changing_clean_programs(self):
        fixture=json.loads((ROOT/'tests/fixtures/display-motion-rounding.json').read_text(encoding='utf-8'))
        builder=FontBuilderCore(fixture['cut'],display=True);builder.F=fixture['contrast']
        path=builder.outline(fixture['record'],0)
        def decode(cs):
            cs.private=SimpleNamespace(nominalWidthX=0,defaultWidthX=0,Subrs=[]);cs.globalSubrs=[]
            result=pathops.Path();cs.draw(result.getPen());return result
        with patch('font_builder.repair_quantized_edges',side_effect=lambda cs,advance:cs):
            original=builder.charstring(path,1000)
        self.assertTrue(any(flag['kind']=='tiny-segment' for flag in flags(decode(original))))
        repaired=builder.charstring(path,1000)
        self.assertEqual(flags(decode(repaired)),[])
        from display.outline_cleanup import repair_quantized_edges
        self.assertIs(repair_quantized_edges(repaired,1000),repaired)

    def test_fractional_weight_failure_is_repaired_without_a_glyph_exception(self):
        fixture=json.loads((ROOT/'tests/fixtures/display-motion-union.json').read_text(encoding='utf-8'))
        builder=FontBuilderCore(fixture['cut'],display=True)
        builder.F=max(fixture['cut']['contrast'],fixture['cut']['weight']/(fixture['cut']['xHeight']*.2))
        with patch('font_builder.display_union',side_effect=lambda a,b:pathops.op(a,b,pathops.PathOp.UNION,fix_winding=True)):
            with self.assertRaises(pathops.PathOpsError):builder.outline(fixture['record'],0)
        result=builder.outline(fixture['record'],0)
        self.assertTrue(result)
        self.assertEqual(flags(result),[])
        self.assertGreater(abs(result.area),1_000_000)
        self.assertLess(abs(result.area),1_050_000)

    def test_successful_union_is_the_original_exact_result(self):
        first=pathops.Path();first.getPen().moveTo((0,0));first.getPen().lineTo((100,0));first.getPen().lineTo((100,100));first.getPen().closePath()
        second=first.transform(translateX=50)
        expected=pathops.op(first,second,pathops.PathOp.UNION,fix_winding=True)
        actual=display_union(first,second)
        self.assertEqual(list(actual.segments),list(expected.segments))

    def test_unrecoverable_union_fails_instead_of_dropping_ink(self):
        first=pathops.Path();first.getPen().moveTo((0,0));first.getPen().lineTo((10,10));first.getPen().closePath()
        with patch('display.outline_cleanup.pathops.op',side_effect=pathops.PathOpsError('unrecoverable')):
            with self.assertRaises(pathops.PathOpsError):display_union(first,first)


if __name__=='__main__':unittest.main()
