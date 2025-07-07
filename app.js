// DXF CAD Analyzer Web Application JavaScript

// Sample data for chart
const sampleEntityData = {
    LINE: 456,
    TEXT: 156,
    POLYLINE: 89,
    POINT: 234,
    INSERT: 67,
    DIMENSION: 45,
    CIRCLE: 28,
    ARC: 34,
    MTEXT: 23,
    ELLIPSE: 12
};

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    initializeChart();
    setupFileUpload();
    setupSmoothScrolling();
});

// Chart initialization
function initializeChart() {
    const ctx = document.getElementById('entityChart');
    if (!ctx) return;

    const labels = Object.keys(sampleEntityData);
    const data = Object.values(sampleEntityData);
    const colors = ['#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F', '#DB4545', '#D2BA4C', '#964325', '#944454', '#13343B'];

    new Chart(ctx, {
        type: 'doughnut',
        data: {
            labels: labels,
            datasets: [{
                data: data,
                backgroundColor: colors.slice(0, labels.length),
                borderWidth: 2,
                borderColor: '#fff'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: true,
            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        padding: 15,
                        usePointStyle: true,
                        font: {
                            size: 12
                        }
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed;
                            const total = context.dataset.data.reduce((a, b) => a + b, 0);
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value}개 (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
}

// Tab switching functionality
function showTab(tabName) {
    // Hide all tab contents
    const tabContents = document.querySelectorAll('.tab-content');
    tabContents.forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all tab buttons
    const tabButtons = document.querySelectorAll('.tab-btn');
    tabButtons.forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected tab content
    const selectedTab = document.getElementById(`${tabName}-tab`);
    if (selectedTab) {
        selectedTab.classList.add('active');
    }

    // Add active class to clicked button
    event.target.classList.add('active');
}

// File upload functionality
function setupFileUpload() {
    const uploadArea = document.getElementById('uploadArea');
    const fileInput = document.getElementById('fileInput');

    if (!uploadArea || !fileInput) return;

    // Click to upload
    uploadArea.addEventListener('click', () => {
        fileInput.click();
    });

    // Drag and drop functionality
    uploadArea.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--color-primary-hover)';
        uploadArea.style.backgroundColor = 'var(--color-secondary)';
    });

    uploadArea.addEventListener('dragleave', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--color-primary)';
        uploadArea.style.backgroundColor = 'var(--color-surface)';
    });

    uploadArea.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadArea.style.borderColor = 'var(--color-primary)';
        uploadArea.style.backgroundColor = 'var(--color-surface)';
        
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    });

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });
}

// Handle file upload simulation
function handleFileUpload(file) {
    const uploadArea = document.getElementById('uploadArea');
    const uploadContent = uploadArea.querySelector('.upload-content');
    
    // Check file type
    const validTypes = ['.dxf', '.dwg'];
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();
    
    if (!validTypes.includes(fileExtension)) {
        showNotification('지원하지 않는 파일 형식입니다. DXF 또는 DWG 파일을 업로드해주세요.', 'error');
        return;
    }

    // Start upload simulation
    uploadArea.classList.add('processing');
    uploadContent.innerHTML = `
        <div class="upload-icon">⏳</div>
        <h3>파일 분석 중...</h3>
        <p>${file.name} (${formatFileSize(file.size)})</p>
        <div class="upload-progress"></div>
    `;

    // Simulate upload progress
    let progress = 0;
    const progressBar = uploadArea.querySelector('.upload-progress');
    const interval = setInterval(() => {
        progress += Math.random() * 15;
        if (progress >= 100) {
            progress = 100;
            clearInterval(interval);
            completeUpload(file);
        }
        progressBar.style.width = `${progress}%`;
    }, 200);
}

// Complete upload simulation
function completeUpload(file) {
    const uploadArea = document.getElementById('uploadArea');
    const uploadContent = uploadArea.querySelector('.upload-content');
    
    uploadContent.innerHTML = `
        <div class="upload-icon">✅</div>
        <h3>분석 완료!</h3>
        <p>${file.name}</p>
        <button class="btn btn--primary" onclick="showAnalysisResults()">결과 보기</button>
    `;

    showNotification('DXF 파일 분석이 완료되었습니다!', 'success');
}

// Show analysis results in modal
function showAnalysisResults() {
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h2>분석 결과</h2>
        <div class="results-summary">
            <h3>파일 정보</h3>
            <div class="stat-item">
                <span class="stat-label">파일명:</span>
                <span class="stat-value">sample_drawing.dxf</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">파일 크기:</span>
                <span class="stat-value">2.5 MB</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">전체 엔티티:</span>
                <span class="stat-value">1,234개</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">레이어 수:</span>
                <span class="stat-value">15개</span>
            </div>
        </div>
        
        <h3>상세 엔티티 분석</h3>
        <div class="entity-details">
            ${Object.entries(sampleEntityData).map(([type, count]) => `
                <div class="stat-item">
                    <span class="stat-label">${type}:</span>
                    <span class="stat-value">${count}개</span>
                </div>
            `).join('')}
        </div>
        
        <h3>생성된 리포트</h3>
        <div class="report-actions">
            <button class="btn btn--primary" onclick="downloadReport('markdown')">마크다운 리포트 다운로드</button>
            <button class="btn btn--outline" onclick="downloadReport('json')">JSON 데이터 다운로드</button>
        </div>
        
        <div class="markdown-preview" style="margin-top: 20px;">
            <pre><code># DXF 분석 리포트

## 파일 정보
- 파일명: sample_drawing.dxf
- 크기: 2.5 MB
- 분석 일시: ${new Date().toLocaleString('ko-KR')}

## 엔티티 통계
- 총 엔티티 수: 1,234개
${Object.entries(sampleEntityData).map(([type, count]) => 
    `- ${type}: ${count}개 (${((count / 1234) * 100).toFixed(1)}%)`
).join('\n')}

## 레이어 정보
- 총 레이어 수: 15개
- 활성 레이어: 12개
- 비활성 레이어: 3개

## 분석 완료
분석이 성공적으로 완료되었습니다.</code></pre>
        </div>
    `;
    
    openModal();
}

// Simulate file upload button click
function simulateFileUpload() {
    const fileInput = document.getElementById('fileInput');
    if (fileInput) {
        fileInput.click();
    }
}

// Download simulation
function simulateDownload(type) {
    let fileName, message;
    
    switch(type) {
        case 'executable':
            fileName = 'dxf-analyzer-v1.0.0-windows.exe';
            message = 'Windows 실행파일 다운로드를 시작합니다.';
            break;
        case 'source':
            fileName = 'dxf-analyzer-source.zip';
            message = '소스 코드 다운로드를 시작합니다.';
            break;
        default:
            fileName = 'download.zip';
            message = '다운로드를 시작합니다.';
    }
    
    showNotification(message, 'info');
    
    // Simulate download
    setTimeout(() => {
        showNotification(`${fileName} 다운로드가 완료되었습니다.`, 'success');
    }, 2000);
}

// Download report simulation
function downloadReport(format) {
    let fileName, message;
    
    if (format === 'markdown') {
        fileName = 'dxf_analysis_report.md';
        message = '마크다운 리포트를 다운로드합니다.';
    } else {
        fileName = 'dxf_analysis_data.json';
        message = 'JSON 데이터를 다운로드합니다.';
    }
    
    showNotification(message, 'info');
    
    // Create and download file
    const content = format === 'markdown' ? generateMarkdownReport() : JSON.stringify(sampleEntityData, null, 2);
    const blob = new Blob([content], { type: format === 'markdown' ? 'text/markdown' : 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = fileName;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    setTimeout(() => {
        showNotification(`${fileName} 다운로드가 완료되었습니다.`, 'success');
    }, 1000);
}

// Generate markdown report
function generateMarkdownReport() {
    return `# DXF 분석 리포트

## 파일 정보
- 파일명: sample_drawing.dxf
- 크기: 2.5 MB
- 분석 일시: ${new Date().toLocaleString('ko-KR')}

## 엔티티 통계
- 총 엔티티 수: 1,234개
${Object.entries(sampleEntityData).map(([type, count]) => 
    `- ${type}: ${count}개 (${((count / 1234) * 100).toFixed(1)}%)`
).join('\n')}

## 레이어 정보
- 총 레이어 수: 15개
- 활성 레이어: 12개
- 비활성 레이어: 3개

## 분석 완료
분석이 성공적으로 완료되었습니다.

---
Generated by DXF CAD 도면 분석기 v1.0.0`;
}

// Show install guide
function showInstallGuide() {
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h2>설치 가이드</h2>
        
        <div class="install-tabs">
            <button class="tab-btn active" onclick="showInstallTab('windows')">Windows</button>
            <button class="tab-btn" onclick="showInstallTab('linux')">Linux/macOS</button>
            <button class="tab-btn" onclick="showInstallTab('manual')">수동 설치</button>
        </div>
        
        <div id="windows-install" class="install-content active">
            <h3>Windows 설치</h3>
            <ol>
                <li>install.bat 파일 다운로드</li>
                <li>관리자 권한으로 실행</li>
                <li>자동 설치 완료 대기</li>
                <li><code>python dxf_analyzer.py --gui</code> 실행</li>
            </ol>
            <button class="btn btn--primary" onclick="simulateDownload('installer')">install.bat 다운로드</button>
        </div>
        
        <div id="linux-install" class="install-content">
            <h3>Linux/macOS 설치</h3>
            <ol>
                <li><code>chmod +x install.sh</code></li>
                <li><code>./install.sh</code> 실행</li>
                <li>의존성 자동 설치</li>
                <li><code>python3 dxf_analyzer.py --gui</code> 실행</li>
            </ol>
            <button class="btn btn--primary" onclick="simulateDownload('installer')">install.sh 다운로드</button>
        </div>
        
        <div id="manual-install" class="install-content">
            <h3>수동 설치</h3>
            <ol>
                <li>Python 3.8+ 설치 확인</li>
                <li><code>pip install -r requirements.txt</code></li>
                <li><code>git clone repository</code></li>
                <li><code>python dxf_analyzer.py --help</code></li>
            </ol>
            <div class="requirements">
                <h4>requirements.txt</h4>
                <pre><code>ezdxf>=1.0.0
pandas>=1.3.0
streamlit>=1.0.0
matplotlib>=3.5.0
plotly>=5.0.0</code></pre>
            </div>
        </div>
    `;
    
    openModal();
}

// Show install tab
function showInstallTab(tabName) {
    // Hide all install contents
    const installContents = document.querySelectorAll('.install-content');
    installContents.forEach(content => {
        content.classList.remove('active');
    });

    // Remove active class from all install tab buttons
    const installTabButtons = document.querySelectorAll('.install-tabs .tab-btn');
    installTabButtons.forEach(btn => {
        btn.classList.remove('active');
    });

    // Show selected install content
    const selectedContent = document.getElementById(`${tabName}-install`);
    if (selectedContent) {
        selectedContent.classList.add('active');
    }

    // Add active class to clicked button
    event.target.classList.add('active');
}

// Show user manual
function showUserManual() {
    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h2>사용자 매뉴얼</h2>
        
        <h3>기본 사용법</h3>
        <div class="manual-section">
            <h4>1. GUI 버전 실행</h4>
            <pre><code>python dxf_analyzer.py --gui</code></pre>
            <p>직관적인 그래픽 인터페이스로 DXF 파일을 분석할 수 있습니다.</p>
        </div>
        
        <div class="manual-section">
            <h4>2. 웹 버전 실행</h4>
            <pre><code>python dxf_analyzer.py --web</code></pre>
            <p>웹 브라우저에서 Streamlit 기반 인터페이스를 사용할 수 있습니다.</p>
        </div>
        
        <div class="manual-section">
            <h4>3. CLI 버전 실행</h4>
            <pre><code>python dxf_analyzer.py --cli input.dxf</code></pre>
            <p>명령줄에서 직접 DXF 파일을 분석하고 리포트를 생성합니다.</p>
        </div>
        
        <h3>고급 옵션</h3>
        <div class="manual-section">
            <h4>출력 형식 지정</h4>
            <pre><code>python dxf_analyzer.py --cli input.dxf --output report.md</code></pre>
            
            <h4>배치 처리</h4>
            <pre><code>python dxf_analyzer.py --batch *.dxf</code></pre>
            
            <h4>상세 로그 출력</h4>
            <pre><code>python dxf_analyzer.py --cli input.dxf --verbose</code></pre>
        </div>
        
        <h3>문제 해결</h3>
        <div class="manual-section">
            <p><strong>Q: 파일을 읽을 수 없다는 오류가 발생합니다.</strong></p>
            <p>A: DXF 파일이 손상되었거나 지원하지 않는 버전일 수 있습니다. AutoCAD에서 다시 저장해보세요.</p>
            
            <p><strong>Q: 분석 결과가 정확하지 않습니다.</strong></p>
            <p>A: 복잡한 블록이나 외부 참조가 포함된 경우 일부 정보가 누락될 수 있습니다.</p>
        </div>
    `;
    
    openModal();
}

// Modal functions
function openModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.style.display = 'block';
        document.body.style.overflow = 'hidden';
    }
}

function closeModal() {
    const modal = document.getElementById('modal');
    if (modal) {
        modal.style.display = 'none';
        document.body.style.overflow = 'auto';
    }
}

// Close modal when clicking outside
window.addEventListener('click', function(event) {
    const modal = document.getElementById('modal');
    if (event.target === modal) {
        closeModal();
    }
});

// Notification system
function showNotification(message, type = 'info') {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    // Create notification element
    const notification = document.createElement('div');
    notification.className = `notification notification--${type}`;
    notification.innerHTML = `
        <div class="notification-content">
            <span class="notification-message">${message}</span>
            <button class="notification-close" onclick="this.parentElement.parentElement.remove()">×</button>
        </div>
    `;
    
    // Add styles
    notification.style.cssText = `
        position: fixed;
        top: 20px;
        right: 20px;
        z-index: 10000;
        padding: 16px 20px;
        border-radius: 8px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        max-width: 400px;
        animation: slideIn 0.3s ease-out;
    `;
    
    // Set colors based on type
    const colors = {
        success: { bg: '#d1f2eb', border: '#27ae60', text: '#1e8449' },
        error: { bg: '#fadbd8', border: '#e74c3c', text: '#c0392b' },
        info: { bg: '#d6eaf8', border: '#3498db', text: '#2874a6' },
        warning: { bg: '#fdeaa7', border: '#f39c12', text: '#d68910' }
    };
    
    const color = colors[type] || colors.info;
    notification.style.backgroundColor = color.bg;
    notification.style.border = `1px solid ${color.border}`;
    notification.style.color = color.text;
    
    // Add animation
    const style = document.createElement('style');
    style.textContent = `
        @keyframes slideIn {
            from { transform: translateX(100%); opacity: 0; }
            to { transform: translateX(0); opacity: 1; }
        }
        .notification-content {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 12px;
        }
        .notification-close {
            background: none;
            border: none;
            font-size: 18px;
            cursor: pointer;
            color: inherit;
            opacity: 0.7;
        }
        .notification-close:hover {
            opacity: 1;
        }
    `;
    document.head.appendChild(style);
    
    // Add to document
    document.body.appendChild(notification);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (notification.parentElement) {
            notification.remove();
        }
    }, 5000);
}

// Smooth scrolling for anchor links
function setupSmoothScrolling() {
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
}

// Utility functions
function formatFileSize(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
}

// Initialize tooltips and other UI enhancements
function initializeUI() {
    // Add loading states to buttons
    document.querySelectorAll('.btn').forEach(btn => {
        btn.addEventListener('click', function() {
            if (!this.classList.contains('loading')) {
                this.classList.add('loading');
                setTimeout(() => {
                    this.classList.remove('loading');
                }, 1000);
            }
        });
    });
}

// Call UI initialization
document.addEventListener('DOMContentLoaded', initializeUI);