import unittest
from pathlib import Path

from examples.example_codes import aForLoop, aIf, aWhileLoop, pAssign
from static_analyze.cfg import StmtCFG

DATA_PATH = Path(__file__).parent / 'data'


class RewriterCase(unittest.TestCase):
    def test_case1(self):
        case1_path = DATA_PATH / 'case1'
        with open(case1_path) as f:
            cfg = StmtCFG.gen_cfg(f.read())

        func = cfg.get_function_by_name("predict")
        print(func)

        self.assertEqual(True, True)

    def test_control_flow(self):
        cfg = StmtCFG.gen_cfg(pAssign)
        print(cfg)

        cfg = StmtCFG.gen_cfg(aIf)
        print(cfg)

        cfg = StmtCFG.gen_cfg(aWhileLoop)
        print(cfg)

        cfg = StmtCFG.gen_cfg(aForLoop)
        print(cfg)

        self.assertEqual(True, True)


if __name__ == '__main__':
    unittest.main()
