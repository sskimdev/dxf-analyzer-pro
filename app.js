// DXF CAD Analyzer Web Application JavaScript

// Global variable to store current analysis data
let currentAnalysisData = null;
let entityChartInstance = null; // To store the chart instance

// API Endpoint
const API_ANALYZE_ENDPOINT = '/api/analyze'; // 실제 API 엔드포인트로 변경해야 합니다.

// Initialize application when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    // Initialize chart with no data initially or with a placeholder
    updateChart(null); // Initialize empty chart
    setupFileUpload();
    setupSmoothScrolling();
});

// Chart update function
function updateChart(analysisData) {
    const ctx = document.getElementById('entityChart');
    if (!ctx) return;

    const entityBreakdown = analysisData ? analysisData.entityBreakdown : {};
    const labels = Object.keys(entityBreakdown);
    const data = Object.values(entityBreakdown);
    const colors = ['#1FB8CD', '#FFC185', '#B4413C', '#ECEBD5', '#5D878F', '#DB4545', '#D2BA4C', '#964325', '#944454', '#13343B'];

    if (entityChartInstance) {
        entityChartInstance.destroy(); // Destroy previous chart instance if exists
    }

    entityChartInstance = new Chart(ctx, {
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
                            if (total === 0) return `${label}: ${value}개 (0%)`; // Avoid division by zero
                            const percentage = ((value / total) * 100).toFixed(1);
                            return `${label}: ${value}개 (${percentage}%)`;
                        }
                    }
                },
                title: {
                    display: labels.length === 0, // Show title if no data
                    text: labels.length === 0 ? '데이터 없음' : '',
                    padding: {
                        top: 10,
                        bottom: 10
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

    uploadArea.addEventListener('click', () => fileInput.click());

    ['dragover', 'dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, preventDefaults, false);
        document.body.addEventListener(eventName, preventDefaults, false); // Prevent browser from opening file
    });

    ['dragenter', 'dragover'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = 'var(--color-primary-hover)';
            uploadArea.style.backgroundColor = 'var(--color-secondary)';
        }, false);
    });

    ['dragleave', 'drop'].forEach(eventName => {
        uploadArea.addEventListener(eventName, () => {
            uploadArea.style.borderColor = 'var(--color-primary)';
            uploadArea.style.backgroundColor = 'var(--color-surface)';
        }, false);
    });

    uploadArea.addEventListener('drop', (e) => {
        const dt = e.dataTransfer;
        const files = dt.files;
        if (files.length > 0) {
            handleFileUpload(files[0]);
        }
    }, false);

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFileUpload(e.target.files[0]);
        }
    });

    function preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }
}

// Handle file upload and API call
async function handleFileUpload(file) {
    const uploadArea = document.getElementById('uploadArea');
    const uploadContent = uploadArea.querySelector('.upload-content');

    const validTypes = ['.dxf']; // DWG는 현재 백엔드에서 지원 안 될 수 있으므로 DXF만 허용
    const fileExtension = '.' + file.name.split('.').pop().toLowerCase();

    if (!validTypes.includes(fileExtension)) {
        showNotification('지원하지 않는 파일 형식입니다. DXF 파일을 업로드해주세요.', 'error');
        return;
    }

    uploadArea.classList.add('processing');
    uploadContent.innerHTML = `
        <div class="upload-icon">⏳</div>
        <h3>파일 분석 중...</h3>
        <p>${file.name} (${formatFileSize(file.size)})</p>
        <div class="upload-progress-bar"><div class="upload-progress"></div></div>
    `;
    const progressBarFill = uploadContent.querySelector('.upload-progress');
    progressBarFill.style.width = '0%';


    const formData = new FormData();
    formData.append('file', file);

    try {
        // Simulate progress for a bit before actual upload for better UX
        let progress = 0;
        const progInterval = setInterval(() => {
            progress += 10;
            if (progress <= 30) { // Simulate initial progress
                progressBarFill.style.width = `${progress}%`;
            } else {
                clearInterval(progInterval);
            }
        }, 100);


        const response = await fetch(API_ANALYZE_ENDPOINT, {
            method: 'POST',
            body: formData,
            // Headers (e.g., for authorization) can be added here if needed
            // headers: { 'Authorization': 'Bearer YOUR_TOKEN' }
        });

        clearInterval(progInterval); // Clear simulation interval
        progressBarFill.style.width = '70%'; // Mark as mostly done after server response starts

        if (!response.ok) {
            const errorData = await response.json().catch(() => ({ message: '알 수 없는 서버 오류 발생' }));
            throw new Error(errorData.message || `서버 오류: ${response.status} ${response.statusText}`);
        }

        const result = await response.json();
        progressBarFill.style.width = '100%';
        handleAnalysisResponse(result, file.name);

    } catch (error) {
        console.error('File upload or analysis error:', error);
        showNotification(`분석 실패: ${error.message}`, 'error');
        uploadArea.classList.remove('processing');
        uploadContent.innerHTML = `
            <div class="upload-icon">❌</div>
            <h3>분석 실패</h3>
            <p>${file.name}</p>
            <button class="btn btn--outline" onclick="setupFileUpload()">다시 시도</button>
        `;
    }
}

// Handle the response from the analysis API
function handleAnalysisResponse(analysisResult, originalFileName) {
    currentAnalysisData = analysisResult; // Store the received data globally
    currentAnalysisData.originalFileName = originalFileName; // Add original file name for display

    const uploadArea = document.getElementById('uploadArea');
    const uploadContent = uploadArea.querySelector('.upload-content');

    uploadArea.classList.remove('processing'); // Remove processing class
    uploadContent.innerHTML = `
        <div class="upload-icon">✅</div>
        <h3>분석 완료!</h3>
        <p>${originalFileName}</p>
        <button class="btn btn--primary" onclick="showAnalysisResults()">결과 보기</button>
    `;

    showNotification('DXF 파일 분석이 완료되었습니다!', 'success');
    updateChart(currentAnalysisData); // Update chart with new data
}


// Show analysis results in modal using currentAnalysisData
function showAnalysisResults() {
    if (!currentAnalysisData) {
        showNotification('표시할 분석 데이터가 없습니다.', 'warning');
        return;
    }

    const { originalFileName, fileSize, totalEntities, layerCount, entityBreakdown, reportContent } = currentAnalysisData;

    const modalBody = document.getElementById('modalBody');
    modalBody.innerHTML = `
        <h2>분석 결과</h2>
        <div class="results-summary">
            <h3>파일 정보</h3>
            <div class="stat-item">
                <span class="stat-label">파일명:</span>
                <span class="stat-value">${originalFileName || 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">파일 크기:</span>
                <span class="stat-value">${fileSize ? formatFileSize(fileSize) : 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">전체 엔티티:</span>
                <span class="stat-value">${totalEntities !== undefined ? totalEntities.toLocaleString() + '개' : 'N/A'}</span>
            </div>
            <div class="stat-item">
                <span class="stat-label">레이어 수:</span>
                <span class="stat-value">${layerCount !== undefined ? layerCount + '개' : 'N/A'}</span>
            </div>
        </div>
        
        <h3>상세 엔티티 분석</h3>
        <div class="entity-details">
            ${entityBreakdown ? Object.entries(entityBreakdown).map(([type, count]) => `
                <div class="stat-item">
                    <span class="stat-label">${type}:</span>
                    <span class="stat-value">${count.toLocaleString()}개</span>
                </div>
            `).join('') : '<p>엔티티 분석 정보 없음</p>'}
        </div>
        
        <h3>생성된 리포트</h3>
        <div class="report-actions">
            <button class="btn btn--primary" onclick="downloadReport('markdown')">마크다운 리포트 다운로드</button>
            <button class="btn btn--outline" onclick="downloadReport('json')">JSON 데이터 다운로드</button>
        </div>
        
        <div class="markdown-preview" style="margin-top: 20px;">
            <h4>마크다운 미리보기:</h4>
            <pre><code>${reportContent || '마크다운 리포트 내용 없음'}</code></pre>
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

// Download report using currentAnalysisData
function downloadReport(format) {
    if (!currentAnalysisData) {
        showNotification('다운로드할 분석 데이터가 없습니다.', 'warning');
        return;
    }

    let fileName, content, mimeType;
    const baseFileName = currentAnalysisData.originalFileName ? currentAnalysisData.originalFileName.split('.').slice(0, -1).join('.') : 'analysis';

    if (format === 'markdown') {
        fileName = `${baseFileName}_report.md`;
        content = currentAnalysisData.reportContent || "# 리포트 내용 없음";
        mimeType = 'text/markdown';
        showNotification('마크다운 리포트를 다운로드합니다.', 'info');
    } else if (format === 'json') {
        fileName = `${baseFileName}_data.json`;
        // JSON 데이터는 currentAnalysisData 전체를 사용하거나, 서버가 제공한 특정 JSON 구조를 따를 수 있음
        // 여기서는 currentAnalysisData 전체를 예시로 사용
        content = JSON.stringify(currentAnalysisData, null, 2);
        mimeType = 'application/json';
        showNotification('JSON 데이터를 다운로드합니다.', 'info');
    } else {
        showNotification('알 수 없는 다운로드 형식입니다.', 'error');
        return;
    }
    
    const blob = new Blob([content], { type: mimeType });
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