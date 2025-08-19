/**
 * 정부지원사업 지역분류 시스템 JavaScript
 */

// 전역 설정
const AppConfig = {
    API_BASE_URL: '',
    DEFAULT_PAGE_SIZE: 20,
    AUTO_REFRESH_INTERVAL: 5 * 60 * 1000 // 5분
};

// 유틸리티 함수들
const Utils = {
    /**
     * 텍스트 자르기
     */
    truncateText: function(text, maxLength) {
        if (!text) return '';
        return text.length > maxLength ? text.substring(0, maxLength) + '...' : text;
    },

    /**
     * 날짜 포맷팅
     */
    formatDate: function(dateString) {
        if (!dateString) return '-';
        const date = new Date(dateString);
        return date.toLocaleDateString('ko-KR');
    },

    /**
     * 숫자 포맷팅 (천단위 구분자)
     */
    formatNumber: function(num) {
        if (!num) return '0';
        return num.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ',');
    },

    /**
     * 로딩 스피너 표시/숨김
     */
    showLoading: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'block';
        }
    },

    hideLoading: function(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.style.display = 'none';
        }
    },

    /**
     * 알림 메시지 표시
     */
    showAlert: function(message, type = 'info', duration = 5000) {
        const alertHtml = `
            <div class="alert alert-${type} alert-dismissible fade show" role="alert">
                ${message}
                <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
            </div>
        `;
        
        // 기존 알림이 있는 곳에 추가
        let alertContainer = document.getElementById('alert-container');
        if (!alertContainer) {
            alertContainer = document.createElement('div');
            alertContainer.id = 'alert-container';
            alertContainer.className = 'container mt-3';
            document.querySelector('main').insertBefore(alertContainer, document.querySelector('main').firstChild);
        }
        
        alertContainer.insertAdjacentHTML('beforeend', alertHtml);
        
        // 자동 삭제
        if (duration > 0) {
            setTimeout(() => {
                const alerts = alertContainer.querySelectorAll('.alert');
                if (alerts.length > 0) {
                    alerts[0].remove();
                }
            }, duration);
        }
    },

    /**
     * API 호출 래퍼
     */
    apiCall: async function(url, options = {}) {
        try {
            const response = await fetch(url, {
                headers: {
                    'Content-Type': 'application/json',
                    ...options.headers
                },
                ...options
            });

            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API call failed:', error);
            throw error;
        }
    }
};

// 공고 관련 기능
const AnnouncementManager = {
    /**
     * 공고 목록 로드
     */
    loadAnnouncements: async function(filters = {}) {
        try {
            Utils.showLoading('loadingSpinner');
            
            const params = new URLSearchParams();
            Object.keys(filters).forEach(key => {
                if (filters[key]) {
                    params.append(key, filters[key]);
                }
            });
            
            const data = await Utils.apiCall(`/api/announcements?${params}`);
            
            if (data.success) {
                this.displayAnnouncements(data.data);
                this.updateResultCount(data.count);
            } else {
                throw new Error(data.error || '데이터 로드 실패');
            }
            
        } catch (error) {
            Utils.showAlert('데이터를 불러오는데 실패했습니다: ' + error.message, 'danger');
            this.displayError(error.message);
        } finally {
            Utils.hideLoading('loadingSpinner');
        }
    },

    /**
     * 공고 목록 표시
     */
    displayAnnouncements: function(announcements) {
        const container = document.getElementById('announcementsList');
        if (!container) return;

        if (!announcements || announcements.length === 0) {
            container.innerHTML = `
                <div class="alert alert-warning">
                    <i class="bi bi-exclamation-triangle"></i>
                    검색 조건에 맞는 지원사업이 없습니다.
                </div>
            `;
            return;
        }

        let html = '';
        announcements.forEach(announcement => {
            html += this.createAnnouncementCard(announcement);
        });

        container.innerHTML = html;
    },

    /**
     * 공고 카드 생성
     */
    createAnnouncementCard: function(announcement) {
        const regionName = announcement.region_name || '미분류';
        const createdDate = Utils.formatDate(announcement.created_at);
        const summary = Utils.truncateText(announcement.bsnsSumryCn || '', 150);
        
        return `
            <div class="card mb-3 announcement-card fade-in">
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-8">
                            <h5 class="card-title">
                                ${announcement.pblancUrl ? 
                                    `<a href="${announcement.pblancUrl}" target="_blank" class="text-decoration-none">${announcement.pblancNm}</a>` :
                                    announcement.pblancNm
                                }
                            </h5>
                            <p class="card-text text-muted small mb-2 text-truncate-2">
                                ${summary}
                            </p>
                            <div class="row small text-muted">
                                <div class="col-sm-6">
                                    <strong>소관기관:</strong> ${announcement.jrsdInsttNm || '-'}
                                </div>
                                <div class="col-sm-6">
                                    <strong>수행기관:</strong> ${announcement.excInsttNm || '-'}
                                </div>
                                <div class="col-sm-6 mt-1">
                                    <strong>신청기간:</strong> ${announcement.reqstBeginEndDe || '-'}
                                </div>
                                <div class="col-sm-6 mt-1">
                                    <strong>등록일:</strong> ${createdDate}
                                </div>
                            </div>
                        </div>
                        <div class="col-md-4 text-md-end">
                            <span class="badge bg-primary mb-2">${regionName}</span><br>
                            ${announcement.pldirSportRealmLclasCodeNm ? 
                                `<span class="badge bg-secondary mb-2">${announcement.pldirSportRealmLclasCodeNm}</span><br>` : ''
                            }
                            <div class="mt-2">
                                ${announcement.pblancUrl ? 
                                    `<a href="${announcement.pblancUrl}" target="_blank" class="btn btn-outline-primary btn-sm">
                                        <i class="bi bi-eye"></i> 공고 보기
                                     </a>` : ''
                                }
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;
    },

    /**
     * 검색 결과 수 업데이트
     */
    updateResultCount: function(count) {
        const element = document.getElementById('resultCount');
        if (element) {
            element.textContent = `${Utils.formatNumber(count)}개 결과`;
        }
    },

    /**
     * 에러 표시
     */
    displayError: function(message) {
        const container = document.getElementById('announcementsList');
        if (container) {
            container.innerHTML = `
                <div class="alert alert-danger">
                    <i class="bi bi-exclamation-triangle"></i>
                    ${message}
                </div>
            `;
        }
    }
};

// 관리자 기능
const AdminManager = {
    /**
     * 수동 분류 수행
     */
    classifyAnnouncement: async function(announcementId, regionCode) {
        try {
            const data = await Utils.apiCall('/admin/classify', {
                method: 'POST',
                body: JSON.stringify({
                    announcement_id: announcementId,
                    region_code: regionCode
                })
            });

            if (data.success) {
                Utils.showAlert('분류가 완료되었습니다.', 'success');
                return true;
            } else {
                throw new Error(data.error || '분류 실패');
            }
        } catch (error) {
            Utils.showAlert('분류 중 오류가 발생했습니다: ' + error.message, 'danger');
            return false;
        }
    },

    /**
     * 데이터 수집 실행
     */
    collectData: async function(searchCount = 20) {
        try {
            Utils.showAlert('데이터 수집을 시작합니다...', 'info');
            
            const data = await Utils.apiCall('/admin/collect', {
                method: 'POST',
                body: JSON.stringify({
                    search_cnt: searchCount
                })
            });

            if (data.success) {
                const result = data.result;
                const message = `
                    수집 완료!<br>
                    • 총 수집: ${result.total_fetched}개<br>
                    • 신규: ${result.new_announcements}개<br>
                    • 키워드 분류: ${result.keyword_classified}개<br>
                    • AI 분류: ${result.ai_classified}개<br>
                    • 분류 실패: ${result.classification_failed}개
                `;
                
                Utils.showAlert(message, 'success', 10000);
                return result;
            } else {
                throw new Error(data.error || '데이터 수집 실패');
            }
        } catch (error) {
            Utils.showAlert('데이터 수집 중 오류가 발생했습니다: ' + error.message, 'danger');
            return null;
        }
    }
};

// 폼 관련 기능
const FormManager = {
    /**
     * 검색 폼 초기화
     */
    initSearchForm: function() {
        const searchForm = document.getElementById('searchForm');
        if (searchForm) {
            searchForm.addEventListener('submit', function(e) {
                e.preventDefault();
                
                const formData = new FormData(searchForm);
                const filters = {};
                
                for (let [key, value] of formData.entries()) {
                    if (value) {
                        filters[key] = value;
                    }
                }
                
                AnnouncementManager.loadAnnouncements(filters);
            });
        }
    },

    /**
     * 필터 폼 초기화
     */
    initFilterForm: function() {
        const filterInputs = document.querySelectorAll('#searchForm select, #searchForm input');
        filterInputs.forEach(input => {
            input.addEventListener('change', function() {
                // 자동 검색 (선택사항)
                // document.getElementById('searchForm').dispatchEvent(new Event('submit'));
            });
        });
    }
};

// 페이지별 초기화
const PageInitializer = {
    /**
     * 메인 페이지 초기화
     */
    initIndexPage: function() {
        // 검색 폼 초기화
        FormManager.initSearchForm();
        FormManager.initFilterForm();
        
        // 초기 데이터 로드
        AnnouncementManager.loadAnnouncements();
    },

    /**
     * 관리자 대시보드 초기화
     */
    initAdminDashboard: function() {
        // 자동 새로고침 설정
        if (window.location.pathname.includes('/admin')) {
            setInterval(() => {
                // 현재 활성 상태인 경우에만 새로고침
                if (document.visibilityState === 'visible') {
                    window.location.reload();
                }
            }, AppConfig.AUTO_REFRESH_INTERVAL);
        }
    },

    /**
     * 공통 초기화
     */
    initCommon: function() {
        // Bootstrap tooltip 초기화
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });

        // 외부 링크 처리
        const externalLinks = document.querySelectorAll('a[target="_blank"]');
        externalLinks.forEach(link => {
            link.setAttribute('rel', 'noopener noreferrer');
        });
    }
};

// DOM 로드 완료시 초기화
document.addEventListener('DOMContentLoaded', function() {
    // 공통 초기화
    PageInitializer.initCommon();
    
    // 페이지별 초기화
    const path = window.location.pathname;
    
    if (path === '/' || path === '/index') {
        PageInitializer.initIndexPage();
    } else if (path.includes('/admin')) {
        PageInitializer.initAdminDashboard();
    }
});

// 전역 에러 핸들러
window.addEventListener('error', function(e) {
    console.error('Global error:', e.error);
    Utils.showAlert('예상치 못한 오류가 발생했습니다.', 'danger');
});

// 전역 객체로 노출
window.App = {
    Utils,
    AnnouncementManager,
    AdminManager,
    FormManager
};