"""
secure_meeting/gui.py
PyQt5 GUI for the secure‑meeting protocol (Alice / Bob / ZY).

依赖:
    pip install pyqt5 sympy
"""
import sys, random, json, base64
from pathlib import Path
from sympy import nextprime, isprime
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QTextEdit, QLineEdit, QMessageBox
)

# ---------- utils (直接内嵌, 也可以 `from utils import ...`) ----------
def generate_large_prime(bits: int = 256):
    import secrets
    return nextprime(secrets.randbits(bits))

def generate_n_random_primes(n: int, upper_bound: int):
    """随机采样 n 个互不相同的小素数 ( < upper_bound )"""
    primes = set()
    while len(primes) < n:
        cand = random.randint(3, upper_bound - 1)
        if isprime(cand):
            primes.add(cand)
    return list(primes)

def encode_data(label: str, data: dict) -> str:
    return f"{label}:{base64.b64encode(json.dumps(data).encode()).decode()}"

def decode_data(encoded: str, expected_label: str) -> dict:
    label, b64 = encoded.split(":", 1)
    assert label == expected_label, f"收到 {label} 但期望 {expected_label}"
    return json.loads(base64.b64decode(b64).decode())

# ---------- GUI ----------
class RoleFrame(QWidget):
    """
    通用角色界面 (Alice / Bob / ZY)，内部用 step 决定当前子阶段，
    每点一次 'CALC'（下一步）就推进一步并刷新导航提示。
    """
    def __init__(self, role: str, back_to_home) -> None:
        super().__init__()
        self.role = role            # 'alice' | 'bob' | 'zy'
        self.step = 0               # 子阶段索引
        self.state = {}             # 运行时缓存
        self.back_cb = back_to_home # 返回首页回调

        # 布局
        v = QVBoxLayout(self)
        title = QLabel(f"<h2>Welcome, {role.title()}</h2>")
        v.addWidget(title)

        # --- 输入区 (单行 or 多行均可) ---
        self.input_label = QLabel("input:")
        self.input_edit  = QTextEdit()
        self.input_edit.setPlaceholderText("在此粘贴/输入 …")
        v.addWidget(self.input_label)
        v.addWidget(self.input_edit)

        # --- 结果区 ---
        self.output_label = QLabel("paste to XXX:")
        self.output_edit  = QTextEdit()
        self.output_edit.setReadOnly(True)
        self.output_edit.setPlaceholderText("程序输出将显示在此, 复制发给下一方")
        v.addWidget(self.output_label)
        v.addWidget(self.output_edit)

        # --- 控制按钮 ---
        h = QHBoxLayout()
        self.calc_btn  = QPushButton("CALC")
        self.back_btn  = QPushButton("Back")
        h.addWidget(self.calc_btn); h.addWidget(self.back_btn)
        v.addLayout(h)

        self.back_btn.clicked.connect(lambda: self.back_cb())
        self.calc_btn.clicked.connect(self.next_step)

        self.update_nav()   # 初始化提示

    # ------- 公共工具 -------
    def alert(self, msg: str):
        QMessageBox.information(self, "提示", msg)

    def update_nav(self):
        """根据角色 + step 更新标签 / 提示文字"""
        guide = {
            ("alice",0): ("input N,available slots", "input first"),
            ("alice",1): ("input B2",                "paste A1 to Bob"),
            ("alice",2): ("input j",                 "paste A2 to ZY"),
            ("alice",3): ("get you result",          "your common time"),
            ("bob"  ,0): ("input A1",                "input first"),
            ("bob"  ,1): ("input available slots",   "paste B1 to ZY"),
            ("bob"  ,2): ("input i",                 "paste B2 to Alice"),
            ("bob"  ,3): ("wait for alice's res",    "paste j to Alice"),
            ("zy"   ,0): ("input B1 and A2 in two line", "input first"),
            ("zy"   ,1): ("waiting for alice's res", "paste i to Bob"),
        }
        inp, out = guide.get((self.role,self.step),("input:","output:"))
        self.input_label.setText(inp)
        self.output_label.setText(out)
        self.input_edit.clear()

    # ------- 主状态机 -------
    def next_step(self):
        try:
            if self.role == "alice":
                self.alice_flow()
            elif self.role == "bob":
                self.bob_flow()
            else:
                self.zy_flow()
            self.update_nav()
        except Exception as e:
            self.alert(str(e))

    # ========== ALICE ==========
    def alice_flow(self):
        if self.step == 0:
            # 解析输入: "N,slot1,slot2,…"
            raw = self.input_edit.toPlainText().strip()
            parts = [x for x in raw.replace("，",",").split() if x]
            assert len(parts)>=2, "请按多行格式输入"
            N = int(parts[0]); slots = list(map(int, parts[1:]))
            p = generate_large_prime(); P = generate_n_random_primes(N,p)
            alpha = random.randint(3, p-3)
            A2   = [P[i-1] for i in slots]
            while len(A2)<N:
                d = nextprime(random.randint(2,p-1))
                if d not in P: A2.append(d)
            M = [pow(x,alpha,p) for x in A2]
            P1 = sorted(range(len(M)), key=M.__getitem__)
            M_sorted = sorted(M)

            self.state.update(N=N,p=p,P=P,alpha=alpha,A2=A2,P1=P1)
            payload = encode_data("A1", {"N":N,"p":p,"P":P,"M_a":M_sorted})
            self.output_edit.setPlainText(payload)
            self.step += 1

        elif self.step == 1:
            enc = self.input_edit.toPlainText().strip()
            M_b = decode_data(enc,"B2")["M_b"]
            alpha,p = self.state["alpha"], self.state["p"]
            M_ba = sorted(pow(m,alpha,p) for m in M_b)
            payload = encode_data("A2", {"M_ba":M_ba})
            self.output_edit.setPlainText(payload)
            self.step += 1

        elif self.step == 2:
            j = int(self.input_edit.toPlainText().strip())
            A2,P1,P = self.state["A2"], self.state["P1"], self.state["P"]
            p_k = A2[P1[j]]; k = P.index(p_k)+1
            self.output_edit.setPlainText(f"共同空闲时间槽索引 k = {k}")
            self.step += 1

    # ========== BOB ==========
    def bob_flow(self):
        if self.step == 0:
            enc = self.input_edit.toPlainText().strip()
            data = decode_data(enc,"A1")
            N,p,P,M_a = data["N"],data["p"],data["P"],data["M_a"]
            beta = random.randint(3,p-3)
            M_ab = [pow(m,beta,p) for m in M_a]
            P2   = sorted(range(len(M_ab)), key=M_ab.__getitem__)
            self.state.update(N=N,p=p,P=P,beta=beta,P2=P2)
            payload = encode_data("B1",{"M_ab":sorted(M_ab)})
            self.output_edit.setPlainText(payload)
            self.step += 1

        elif self.step == 1:
            raw = self.input_edit.toPlainText().strip()
            slots = list(map(int,[x for x in raw.replace("，",",").split() if x]))
            assert len(slots)>=2, "请按多行格式输入"
            N,p,P,beta = self.state["N"],self.state["p"],self.state["P"],self.state["beta"]
            B2 = [P[i-1] for i in slots]
            while len(B2)<N:
                d=nextprime(random.randint(2,p-1))
                if d not in P:B2.append(d)
            M_b = [pow(x,beta,p) for x in B2]
            payload = encode_data("B2",{"M_b":sorted(M_b)})
            self.output_edit.setPlainText(payload)
            self.step += 1

        elif self.step == 2:
            i = int(self.input_edit.toPlainText().strip())
            j = self.state["P2"][i]
            self.output_edit.setPlainText(str(j))
            self.step += 1

    # ========== ZY ==========
    def zy_flow(self):
        if self.step == 0:
            raw = self.input_edit.toPlainText().strip().splitlines()
            assert len(raw)>=2, "请在两行粘贴 B1 与 A2 编码"
            M_ab = decode_data(raw[0].strip(),"B1")["M_ab"]
            M_ba = decode_data(raw[1].strip(),"A2")["M_ba"]
            inter = list(set(M_ab)&set(M_ba))
            if not inter:
                self.output_edit.setPlainText("交集为空")
                return
            z=random.choice(inter); i=M_ab.index(z)
            self.output_edit.setPlainText(f"{i}  (标签: Z1)")
            self.step += 1

# ---------- 主窗 ----------
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Secure‑Meeting Demo")
        self.resize(300,200)
        v=QVBoxLayout(self)
        v.addWidget(QLabel("<h2>APP NAME</h2>",alignment=0x0004))
        v.addWidget(QLabel("choose character",alignment=0x0004))
        btn_a = QPushButton("alice"); btn_b = QPushButton("bob"); btn_z = QPushButton("zy")
        v.addWidget(btn_a); v.addWidget(btn_b); v.addWidget(btn_z)
        btn_a.clicked.connect(lambda:self.open_role("alice"))
        btn_b.clicked.connect(lambda:self.open_role("bob"))
        btn_z.clicked.connect(lambda:self.open_role("zy"))

    def open_role(self,role):
        self.hide()
        self.role_win = RoleFrame(role, self.show)
        self.role_win.show()

# ---------- 运行 ----------
if __name__ == "__main__":
    app = QApplication(sys.argv)
    mw  = MainWindow(); mw.show()
    sys.exit(app.exec_())
