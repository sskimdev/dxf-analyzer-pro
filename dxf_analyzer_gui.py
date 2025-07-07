import sys
import os
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
from pathlib import Path
import threading
import logging
import asyncio # AI 분석 비동기 실행을 위해 추가

# 현재 파일의 디렉토리를 sys.path에 추가하여 동일 레벨의 모듈 임포트
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dxf_analyzer import DXFAnalyzer, ADVANCED_ANALYSIS_AVAILABLE
# 다른 필요한 모듈 임포트 (dxf_analyzer.py에서 GUI 클래스로 이동된 의존성)
try:
    from dxf_comparison import DXFComparison
    COMPARISON_AVAILABLE = True
except ImportError:
    COMPARISON_AVAILABLE = False

try:
    from dxf_auto_fix import DXFAutoFix
    AUTO_FIX_AVAILABLE = True
except ImportError:
    AUTO_FIX_AVAILABLE = False

try:
    from dxf_3d_analyzer import DXF3DAnalyzer
    ANALYZER_3D_AVAILABLE = True
except ImportError:
    ANALYZER_3D_AVAILABLE = False

try:
    from dxf_ai_integration import DXFAIIntegration
    AI_INTEGRATION_AVAILABLE = True
except ImportError:
    AI_INTEGRATION_AVAILABLE = False


logger = logging.getLogger(__name__)

class DXFAnalyzerGUI:
    """
    DXF CAD 도면 분석을 위한 Tkinter 기반 그래픽 사용자 인터페이스(GUI)입니다.

    이 클래스는 DXF 파일 선택, 분석 실행, 결과 표시, 리포트 저장 및
    부가 기능(도면 비교, 자동 수정, 3D 분석, AI 기반 분석) 접근을 위한
    메뉴와 위젯을 제공합니다. 핵심 분석 로직은 `DXFAnalyzer` 클래스를 사용합니다.
    """

    def __init__(self, root: tk.Tk):
        """
        DXFAnalyzerGUI의 인스턴스를 초기화합니다.

        Args:
            root (tk.Tk): GUI의 메인 Tkinter 윈도우 객체입니다.
        """
        self.root = root
        self.analyzer = DXFAnalyzer() # 핵심 분석기 인스턴스
        self.setup_window()
        self.create_widgets()

    def setup_window(self):
        """윈도우 설정"""
        self.root.title("DXF CAD 도면 분석기 v2.0.0 - Enhanced Edition")
        self.root.geometry("900x700")
        self.root.minsize(700, 500)

        # 스타일 설정
        style = ttk.Style()
        if 'clam' in style.theme_names():
            style.theme_use('clam')

        # 메뉴 생성
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)

        # 파일 메뉴
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="파일", menu=file_menu)
        file_menu.add_command(label="열기", command=self.browse_file)
        if COMPARISON_AVAILABLE:
            file_menu.add_command(label="비교", command=self.compare_files)
        file_menu.add_separator()
        file_menu.add_command(label="종료", command=self.root.quit)

        # 도구 메뉴
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="도구", menu=tools_menu)
        if AUTO_FIX_AVAILABLE:
            tools_menu.add_command(label="자동 수정", command=self.auto_fix)
        if ANALYZER_3D_AVAILABLE:
            tools_menu.add_command(label="3D 분석", command=self.analyze_3d)
        if AUTO_FIX_AVAILABLE or ANALYZER_3D_AVAILABLE:
             tools_menu.add_separator()
        if AI_INTEGRATION_AVAILABLE:
            tools_menu.add_command(label="AI 분석", command=self.ai_analysis)

        # API 메뉴
        # dxf_cloud_api.py가 존재하고 실행 가능한 경우에만 메뉴를 활성화 할 수 있음 (선택적)
        api_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="API", menu=api_menu)
        api_menu.add_command(label="서버 시작", command=self.start_api_server)
        api_menu.add_command(label="API 문서", command=self.show_api_docs)

    def create_widgets(self):
        """GUI 위젯 생성"""
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky="wens")

        # 파일 선택 섹션
        file_frame = ttk.LabelFrame(main_frame, text="파일 선택", padding="10")
        file_frame.grid(row=0, column=0, sticky="we", pady=(0, 10))

        self.file_var = tk.StringVar()
        file_entry = ttk.Entry(file_frame, textvariable=self.file_var, width=50)
        file_entry.grid(row=0, column=0, padx=(0, 10))

        browse_btn = ttk.Button(file_frame, text="찾아보기", command=self.browse_file)
        browse_btn.grid(row=0, column=1)

        analyze_btn = ttk.Button(file_frame, text="분석 시작", command=self.analyze_file)
        analyze_btn.grid(row=0, column=2, padx=(10, 0))

        # 진행률 표시
        self.progress = ttk.Progressbar(file_frame, mode='indeterminate')
        self.progress.grid(row=1, column=0, columnspan=3, sticky="we", pady=(10, 0))

        # 결과 표시 섹션 (탭 구조로 변경)
        result_frame = ttk.LabelFrame(main_frame, text="분석 결과", padding="10")
        result_frame.grid(row=1, column=0, sticky="wens", pady=(0, 10))

        # 탭 컨트롤 생성
        self.notebook = ttk.Notebook(result_frame)
        self.notebook.grid(row=0, column=0, sticky="wens")

        # 기본 분석 탭
        basic_tab = ttk.Frame(self.notebook)
        self.notebook.add(basic_tab, text="기본 분석")

        self.result_text = tk.Text(basic_tab, wrap=tk.WORD, width=70, height=20)
        scrollbar1 = ttk.Scrollbar(basic_tab, orient=tk.VERTICAL, command=self.result_text.yview)
        self.result_text.configure(yscrollcommand=scrollbar1.set)

        self.result_text.grid(row=0, column=0, sticky="wens")
        scrollbar1.grid(row=0, column=1, sticky="ns")

        # 고급 분석 탭 (고급 분석 가능한 경우만)
        if ADVANCED_ANALYSIS_AVAILABLE:
            advanced_tab = ttk.Frame(self.notebook)
            self.notebook.add(advanced_tab, text="고급 분석")

            self.advanced_text = tk.Text(advanced_tab, wrap=tk.WORD, width=70, height=20)
            scrollbar2 = ttk.Scrollbar(advanced_tab, orient=tk.VERTICAL, command=self.advanced_text.yview)
            self.advanced_text.configure(yscrollcommand=scrollbar2.set)

            self.advanced_text.grid(row=0, column=0, sticky="wens")
            scrollbar2.grid(row=0, column=1, sticky="ns")

            # 탭 프레임 가중치 설정
            advanced_tab.columnconfigure(0, weight=1)
            advanced_tab.rowconfigure(0, weight=1)
        else:
            self.advanced_text = None # 명시적으로 None 할당

        # 탭 프레임 가중치 설정
        basic_tab.columnconfigure(0, weight=1)
        basic_tab.rowconfigure(0, weight=1)

        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.grid(row=2, column=0, sticky="we")

        save_btn = ttk.Button(button_frame, text="리포트 저장", command=self.save_report)
        save_btn.grid(row=0, column=0, padx=(0, 10))

        clear_btn = ttk.Button(button_frame, text="결과 지우기", command=self.clear_results)
        clear_btn.grid(row=0, column=1)

        # 그리드 가중치 설정
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(0, weight=1)
        main_frame.rowconfigure(1, weight=1)
        file_frame.columnconfigure(0, weight=1) # 파일 입력 필드가 늘어나도록
        result_frame.columnconfigure(0, weight=1)
        result_frame.rowconfigure(0, weight=1)

    def browse_file(self):
        """파일 찾아보기"""
        filename = filedialog.askopenfilename(
            title="DXF 파일 선택",
            filetypes=[("DXF files", "*.dxf"), ("All files", "*.*")]
        )
        if filename:
            self.file_var.set(filename)

    def analyze_file(self):
        """파일 분석 (별도 스레드에서 실행)"""
        file_path = self.file_var.get().strip()
        if not file_path:
            messagebox.showwarning("경고", "분석할 파일을 선택해주세요.")
            return

        if not Path(file_path).exists():
            messagebox.showerror("오류", "선택한 파일이 존재하지 않습니다.")
            return

        # 분석을 별도 스레드에서 실행
        self.progress.start()
        thread = threading.Thread(target=self._analyze_worker, args=(file_path,))
        thread.daemon = True # 메인 스레드 종료 시 함께 종료
        thread.start()

    def _analyze_worker(self, file_path):
        """분석 작업 스레드"""
        try:
            success = self.analyzer.analyze_dxf_file(file_path)
            # UI 업데이트는 메인 스레드에서 실행하도록 예약
            self.root.after(0, self._analysis_complete, success)
        except Exception as e:
            logger.error(f"분석 워커 스레드 오류: {e}", exc_info=True)
            self.root.after(0, self._analysis_error, str(e))

    def _analysis_complete(self, success):
        """분석 완료 처리"""
        self.progress.stop()
        if success:
            self.display_results()
            messagebox.showinfo("완료", "DXF 파일 분석이 완료되었습니다!")
        else:
            messagebox.showerror("오류", "DXF 파일 분석에 실패했습니다.")

    def _analysis_error(self, error_msg):
        """분석 오류 처리"""
        self.progress.stop()
        messagebox.showerror("오류", f"분석 중 오류가 발생했습니다:\n{error_msg}")

    def display_results(self):
        """결과 표시"""
        content = self.analyzer._build_markdown_content()
        self.result_text.delete(1.0, tk.END)
        self.result_text.insert(1.0, content)

        if ADVANCED_ANALYSIS_AVAILABLE and self.advanced_text and self.analyzer.analysis_data and self.analyzer.advanced_analyzer:
            try:
                advanced_content = self.analyzer.advanced_analyzer.export_for_ai(
                    self.analyzer.analysis_data,
                    format='markdown'
                )
                self.advanced_text.delete(1.0, tk.END)
                self.advanced_text.insert(1.0, advanced_content)

                ai_context = self.analyzer.advanced_analyzer.generate_ai_context(self.analyzer.analysis_data)
                quality_score = ai_context.get('summary', {}).get('quality_score', 0) # 기본값 0

                # Notebook의 두 번째 탭 (인덱스 1)의 텍스트 변경
                # 탭이 존재하는지 확인
                if self.notebook.index("end") > 1: # 탭이 2개 이상 있을 때
                    tab_id = self.notebook.tabs()[1] # 두 번째 탭의 ID 가져오기
                    if quality_score < 60:
                        self.notebook.tab(tab_id, text="고급 분석 ⚠️")
                    elif quality_score >= 90:
                        self.notebook.tab(tab_id, text="고급 분석 ✅")
                    else:
                        self.notebook.tab(tab_id, text="고급 분석")
            except Exception as e:
                logger.error(f"고급 분석 결과 표시 중 오류: {e}", exc_info=True)
                self.advanced_text.delete(1.0, tk.END)
                self.advanced_text.insert(1.0, f"고급 분석 결과를 표시하는 중 오류 발생:\n{str(e)}")

    def save_report(self):
        """리포트 저장"""
        if not self.analyzer.summary_info: # 분석 결과가 있는지 확인
            messagebox.showwarning("경고", "저장할 분석 결과가 없습니다.")
            return

        filename = filedialog.asksaveasfilename(
            title="리포트 저장",
            defaultextension=".md",
            filetypes=[("Markdown files", "*.md"), ("Text files", "*.txt"), ("All files", "*.*")]
        )
        if filename:
            # generate_advanced_report를 호출하여 AI 컨텍스트 JSON도 함께 저장되도록 함
            if ADVANCED_ANALYSIS_AVAILABLE and self.analyzer.advanced_analyzer:
                 result_path = self.analyzer.generate_advanced_report(filename)
            else:
                 result_path = self.analyzer.generate_markdown_report(filename)

            if result_path:
                messagebox.showinfo("완료", f"리포트가 저장되었습니다:\n{filename}")
            else:
                messagebox.showerror("오류", "리포트 저장에 실패했습니다.")

    def clear_results(self):
        """결과 지우기"""
        self.result_text.delete(1.0, tk.END)
        if self.advanced_text:
            self.advanced_text.delete(1.0, tk.END)
        self.analyzer.reset_analysis_data()
        # 고급 분석 탭 제목 초기화 (존재하는 경우)
        if ADVANCED_ANALYSIS_AVAILABLE and self.notebook.index("end") > 1:
            tab_id = self.notebook.tabs()[1]
            self.notebook.tab(tab_id, text="고급 분석")

    def compare_files(self):
        """두 DXF 파일 비교"""
        if not COMPARISON_AVAILABLE:
            messagebox.showinfo("정보", "도면 비교 기능을 사용할 수 없습니다.")
            return

        file1 = filedialog.askopenfilename(title="첫 번째 DXF 파일 선택", filetypes=[("DXF files", "*.dxf")])
        if not file1: return
        file2 = filedialog.askopenfilename(title="두 번째 DXF 파일 선택", filetypes=[("DXF files", "*.dxf")])
        if not file2: return

        try:
            analyzer1 = DXFAnalyzer()
            analyzer2 = DXFAnalyzer()
            if not analyzer1.analyze_dxf_file(file1) or not analyzer2.analyze_dxf_file(file2):
                messagebox.showerror("오류", "파일 분석에 실패했습니다.")
                return

            comparator = DXFComparison()
            comparator.compare_dxf_files(analyzer1.analysis_data, analyzer2.analysis_data) # 수정: differences 변수 제거
            report = comparator.generate_comparison_report()

            self.result_text.delete(1.0, tk.END)
            self.result_text.insert(1.0, report)
            self.notebook.select(0) # 기본 분석 탭으로 전환
            messagebox.showinfo("완료", "파일 비교가 완료되었습니다!")
        except Exception as e:
            logger.error(f"파일 비교 중 오류: {e}", exc_info=True)
            messagebox.showerror("오류", f"파일 비교 중 오류 발생: {str(e)}")

    def auto_fix(self):
        """자동 수정"""
        if not AUTO_FIX_AVAILABLE:
            messagebox.showinfo("정보", "자동 수정 기능을 사용할 수 없습니다.")
            return
        if not self.analyzer.analysis_data:
            messagebox.showwarning("경고", "먼저 파일을 분석해주세요.")
            return

        file_path_str = self.file_var.get()
        if not file_path_str:
            messagebox.showwarning("경고", "분석된 파일 경로가 없습니다.")
            return

        file_path = Path(file_path_str)

        try:
            fixer = DXFAutoFix()
            if fixer.load_file(str(file_path)):
                backup_path = fixer.create_backup(str(file_path))

                # advanced_analyzer가 DXFAnalyzer 인스턴스 내에 있으므로 이를 전달
                fixes = fixer.auto_fix_all(self.analyzer.analysis_data, self.analyzer.advanced_analyzer)

                fixed_path_str = str(file_path.with_name(f"{file_path.stem}_fixed{file_path.suffix}"))
                fixer.save_fixed_file(fixed_path_str)

                report = fixer.generate_fix_report(fixes)
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, report)
                self.notebook.select(0) # 기본 분석 탭으로 전환
                messagebox.showinfo("완료", f"자동 수정 완료!\n백업: {backup_path}\n수정된 파일: {fixed_path_str}")
            else:
                messagebox.showerror("오류", "자동 수정할 파일을 불러오는데 실패했습니다.")
        except Exception as e:
            logger.error(f"자동 수정 중 오류: {e}", exc_info=True)
            messagebox.showerror("오류", f"자동 수정 중 오류 발생: {str(e)}")

    def analyze_3d(self):
        """3D 분석"""
        if not ANALYZER_3D_AVAILABLE:
            messagebox.showinfo("정보", "3D 분석 기능을 사용할 수 없습니다.")
            return
        if not self.analyzer.analysis_data: # 먼저 2D 분석이 되었는지 확인
            messagebox.showwarning("경고", "먼저 DXF 파일을 분석해주세요.")
            return

        try:
            analyzer_3d = DXF3DAnalyzer()
            # msp 객체를 얻기 위해 파일을 다시 로드해야 할 수 있음, 또는 DXFAnalyzer가 msp를 저장하도록 수정
            # 여기서는 간단히 메시지만 표시 (추후 실제 분석 로직 연동 필요)
            # result_3d = analyzer_3d.analyze_3d_entities(msp_object, self.analyzer.analysis_data)
            # report_3d = analyzer_3d.generate_3d_report(result_3d)
            # self.result_text.delete(1.0, tk.END)
            # self.result_text.insert(1.0, report_3d)
            # self.notebook.select(0)
            messagebox.showinfo("3D 분석", "3D 분석 기능은 현재 개발 중입니다. "
                                        "분석된 데이터가 있다면 콘솔에서 확인할 수 있습니다.")
            # 예시: 콘솔에 로그 출력
            logger.info("3D 분석 요청됨 (현재는 메시지만 표시)")
        except Exception as e:
            logger.error(f"3D 분석 중 오류: {e}", exc_info=True)
            messagebox.showerror("오류", f"3D 분석 중 오류 발생: {str(e)}")

    def ai_analysis(self):
        """AI 분석"""
        if not AI_INTEGRATION_AVAILABLE:
            messagebox.showinfo("정보", "AI 분석 기능을 사용할 수 없습니다.")
            return
        if not self.analyzer.analysis_data:
            messagebox.showwarning("경고", "먼저 파일을 분석해주세요.")
            return

        try:
            ai_integration = DXFAIIntegration()
            if not ai_integration.is_api_key_configured():
                messagebox.showwarning("API 키 필요",
                                       "AI 분석을 위해 OPENAI_API_KEY 또는 ANTHROPIC_API_KEY 환경변수를 설정해야 합니다.")
                return

            self.progress.start()

            # AI 분석을 비동기로 실행하고 결과를 GUI에 업데이트
            thread = threading.Thread(target=self._run_ai_analysis_async, args=(ai_integration,))
            thread.daemon = True
            thread.start()

        except Exception as e:
            self.progress.stop() # 오류 발생 시 프로그레스 바 중지
            logger.error(f"AI 분석 시작 중 오류: {e}", exc_info=True)
            messagebox.showerror("오류", f"AI 분석 시작 중 오류 발생: {str(e)}")

    def _run_ai_analysis_async(self, ai_integration):
        """AI 분석을 비동기적으로 실행하는 내부 메서드"""
        async def job():
            return await ai_integration.analyze_with_both(
                self.analyzer.analysis_data, 'analysis' # 'context_type' 인자 추가
            )

        try:
            # 새 이벤트 루프에서 비동기 작업 실행
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(job())
            loop.close()
            self.root.after(0, self._ai_analysis_complete, result, ai_integration)
        except Exception as e:
            self.root.after(0, self._ai_analysis_error, str(e))


    def _ai_analysis_complete(self, result, ai_integration):
        """AI 분석 완료 콜백"""
        self.progress.stop()
        if 'error' in result:
            messagebox.showerror("AI 분석 오류", result['error'])
        else:
            report = ai_integration.generate_ai_report(result)
            # AI 분석 결과를 고급 분석 탭에 표시 (존재하는 경우)
            if self.advanced_text:
                self.advanced_text.delete(1.0, tk.END)
                self.advanced_text.insert(1.0, report)
                self.notebook.select(1) # 고급 분석 탭으로 전환
            else: # 고급 분석 탭이 없으면 기본 분석 탭에 표시
                self.result_text.delete(1.0, tk.END)
                self.result_text.insert(1.0, report)
                self.notebook.select(0) # 기본 분석 탭으로 전환
            messagebox.showinfo("완료", "AI 분석이 완료되었습니다!")

    def _ai_analysis_error(self, error_msg):
        """AI 분석 오류 콜백"""
        self.progress.stop()
        messagebox.showerror("AI 분석 오류", f"AI 분석 중 오류 발생: {error_msg}")
        logger.error(f"AI 분석 비동기 실행 중 오류: {error_msg}")

    def start_api_server(self):
        """API 서버 시작"""
        try:
            import subprocess

            api_file = Path("dxf_cloud_api.py")
            if not api_file.exists():
                messagebox.showerror("오류", f"{api_file}을 찾을 수 없습니다.")
                return

            # Python 실행 파일 경로를 sys.executable로 명시
            subprocess.Popen([sys.executable, str(api_file)])
            messagebox.showinfo("정보", "API 서버가 시작되었습니다 (백그라운드 실행).\nhttp://localhost:8000/docs 에서 확인하세요.")
        except Exception as e:
            logger.error(f"API 서버 시작 중 오류: {e}", exc_info=True)
            messagebox.showerror("오류", f"API 서버 시작 중 오류 발생: {str(e)}")

    def show_api_docs(self):
        """API 문서 표시"""
        try:
            import webbrowser
            webbrowser.open("http://localhost:8000/docs")
        except Exception as e:
            logger.error(f"API 문서 열기 중 오류: {e}", exc_info=True)
            messagebox.showerror("오류", f"API 문서를 여는 중 오류 발생: {str(e)}")

if __name__ == '__main__':
    # 이 파일이 직접 실행될 때 GUI를 시작 (테스트 목적)
    if not tk.TkVersion:
         logger.error("tkinter 사용 불가. GUI를 실행할 수 없습니다.")
    else:
        root = tk.Tk()
        # 로깅 기본 설정 (GUI 단독 실행 시)
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(module)s - %(message)s')
        logger.info("DXFAnalyzerGUI 단독 실행 모드")

        # 의존성 확인 (dxf_analyzer.py의 check_dependencies와 유사하게)
        # 이 부분은 DXFAnalyzerGUI가 dxf_analyzer 모듈에 의존하므로,
        # dxf_analyzer.py의 check_dependencies를 호출하거나 유사한 로직을 여기에 구현할 수 있습니다.
        # 여기서는 dxf_analyzer.py의 main 함수에서 처리한다고 가정합니다.

        app = DXFAnalyzerGUI(root)
        root.mainloop()
