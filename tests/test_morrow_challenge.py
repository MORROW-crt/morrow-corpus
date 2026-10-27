import unittest,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))
from morrow_challenge import solve

class ChallengeTests(unittest.TestCase):
    def test_obfuscated_subtraction(self):
        self.assertEqual(solve("A] lO^bSt-Er S[wImS aT/ tW]eNn-Tyy mE^tE[rS aNd] SlO/wS bY^ fI[vE, wH-aTs] ThE/ nEw^ SpE[eD?"),"15.00")
    def test_longer_subtraction(self):
        self.assertEqual(solve("A lobster swims at twenty three meters per minute and slows by seven. What is the new speed?"),"16.00")
    def test_multiplication(self):
        self.assertEqual(solve("Claw force is thirty five newtons per pinch and two pinches. Total force?"),"70.00")
    def test_addition(self):
        self.assertEqual(solve("Claw force is fifty newtons and the other claw is twenty four newtons, total force?"),"74.00")
    def test_ambiguous(self):
        with self.assertRaises(ValueError):
            solve("A lobster swims at ten meters and another has nine fish.")
    def test_too_many(self):
        with self.assertRaises(ValueError):
            solve("Two lobsters each have five claws and three eggs total?")
if __name__=="__main__":unittest.main()
