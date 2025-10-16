/**
 * 海心AI工具集 - 智能导航组件
 * 支持：
 * 1. 鼠标悬停显示工具集下拉菜单
 * 2. 同工具集内页面在当前标签页跳转
 * 3. 不同工具集在新标签页打开
 */

class HaixinNav {
	constructor() {
	  this.menuData = null;
	  this.currentToolId = null;
	  this.currentPageKey = null;
	  this.init();
	}
  
	async init() {
	  await this.loadMenuData();
	  this.detectCurrentPage();
	  this.renderNav();
	  this.bindEvents();
	}
  
	/**
	 * 加载菜单配置数据
	 */
	async loadMenuData() {
	  try {
		const response = await fetch('/ai-model-compare/menus');
		this.menuData = await response.json();
	  } catch (error) {
		console.error('加载菜单配置失败:', error);
		// 使用默认配置
		this.menuData = this.getDefaultMenuData();
	  }
	}
  
	/**
	 * 获取默认菜单配置
	 */
	getDefaultMenuData() {
	  return {
		brand: {
		  title: "海心AI工具集",
		  link: "/ai-model-compare/ui"
		},
		tools: [
		  {
			id: "ai-model-compare",
			name: "AI模型对比",
			icon: "🤖",
			pages: [
			  { key: "compare", title: "模型对比", path: "/ai-model-compare/ui", icon: "🔬" },
			  { key: "models", title: "模型管理", path: "/ai-model-compare/models-ui", icon: "⚙️" },
			  { key: "history", title: "对比历史", path: "/ai-model-compare/history-ui", icon: "📜" }
			]
		  }
		]
	  };
	}
  
	/**
	 * 检测当前所在的工具集和页面
	 */
	detectCurrentPage() {
	  const path = window.location.pathname;
	  
	  for (const tool of this.menuData.tools || []) {
		for (const page of tool.pages || []) {
		  if (path === page.path || path.startsWith(page.path + '/')) {
			this.currentToolId = tool.id;
			this.currentPageKey = page.key;
			return;
		  }
		}
	  }
	}
  
	/**
	 * 渲染导航栏
	 */
	renderNav() {
	  const navContainer = document.getElementById('haixin-nav');
	  if (!navContainer) return;
  
	  const html = `
		<nav class="haixin-navbar">
		  <div class="nav-container">
			<!-- 品牌Logo -->
			<div class="nav-brand">
			  <span class="brand-text">${this.menuData.brand.title}</span>
			  <svg class="dropdown-icon" width="12" height="12" viewBox="0 0 12 12" fill="none">
				<path d="M2 4L6 8L10 4" stroke="currentColor" stroke-width="2" stroke-linecap="round"/>
			  </svg>
			</div>
  
			<!-- 工具集下拉菜单 -->
			<div class="nav-dropdown">
			  ${this.renderToolsMenu()}
			</div>
  
			<!-- 当前工具的页面导航 -->
			<div class="nav-pages">
			  ${this.renderCurrentToolPages()}
			</div>
			
			<!-- 开发者接入按钮 -->
			<div class="nav-actions">
			  <a href="/integration-guide" target="_blank" class="dev-guide-btn">
				🔧 开发者接入
			  </a>
			</div>
		  </div>
		</nav>
	  `;
  
	  navContainer.innerHTML = html;
	}
  
	/**
	 * 渲染工具集下拉菜单
	 */
	renderToolsMenu() {
	  const tools = this.menuData.tools || [];
	  
	  return `
		<div class="dropdown-menu">
		  ${tools.map(tool => `
			<div class="tool-group" data-tool-id="${tool.id}">
			  <div class="tool-header">
				<span class="tool-icon">${tool.icon}</span>
				<div class="tool-info">
				  <div class="tool-name">${tool.name}</div>
				  ${tool.description ? `<div class="tool-desc">${tool.description}</div>` : ''}
				  ${tool.owner ? `
					<div class="tool-owner">
					  <span class="owner-icon">👤</span>
					  <span class="owner-info">
						${tool.owner.name}${tool.owner.contact ? ` · ${tool.owner.contact}` : ''}${tool.owner.email ? ` · <a href="mailto:${tool.owner.email}" class="owner-email" onclick="event.stopPropagation()">${tool.owner.email}</a>` : ''}
					  </span>
					</div>
				  ` : ''}
				</div>
			  </div>
			  <div class="tool-pages">
				${(tool.pages || []).map(page => `
				  <a href="${page.path}" 
					 class="page-link ${this.isCurrentPage(tool.id, page.key) ? 'active' : ''}"
					 data-tool-id="${tool.id}"
					 data-page-key="${page.key}">
					<span class="page-icon">${page.icon}</span>
					<span class="page-title">${page.title}</span>
				  </a>
				`).join('')}
			  </div>
			</div>
		  `).join('<div class="tool-divider"></div>')}
		</div>
	  `;
	}
  
	/**
	 * 渲染当前工具的页面导航
	 */
	renderCurrentToolPages() {
	  if (!this.currentToolId) return '';
  
	  const currentTool = (this.menuData.tools || []).find(t => t.id === this.currentToolId);
	  if (!currentTool) return '';
  
	  return (currentTool.pages || []).map(page => `
		<a href="${page.path}" 
		   class="nav-page-link ${this.isCurrentPage(this.currentToolId, page.key) ? 'active' : ''}"
		   data-tool-id="${currentTool.id}"
		   data-page-key="${page.key}">
		  <span class="page-icon">${page.icon}</span>
		  <span class="page-title">${page.title}</span>
		</a>
	  `).join('');
	}
  
	/**
	 * 判断是否为当前页面
	 */
	isCurrentPage(toolId, pageKey) {
	  return this.currentToolId === toolId && this.currentPageKey === pageKey;
	}
  
	/**
	 * 绑定事件
	 */
	bindEvents() {
	  const navBrand = document.querySelector('.nav-brand');
	  const navDropdown = document.querySelector('.nav-dropdown');
	  
	  if (!navBrand || !navDropdown) return;
  
	  let hideTimer = null;
  
	  // 鼠标进入品牌区域，显示下拉菜单
	  navBrand.addEventListener('mouseenter', () => {
		clearTimeout(hideTimer);
		navDropdown.classList.add('show');
		navBrand.classList.add('active');
	  });
  
	  // 鼠标离开品牌区域
	  navBrand.addEventListener('mouseleave', () => {
		hideTimer = setTimeout(() => {
		  if (!navDropdown.matches(':hover')) {
			navDropdown.classList.remove('show');
			navBrand.classList.remove('active');
		  }
		}, 200);
	  });
  
	  // 鼠标进入下拉菜单
	  navDropdown.addEventListener('mouseenter', () => {
		clearTimeout(hideTimer);
	  });
  
	  // 鼠标离开下拉菜单
	  navDropdown.addEventListener('mouseleave', () => {
		navDropdown.classList.remove('show');
		navBrand.classList.remove('active');
	  });
  
	  // 处理链接点击事件
	  this.bindLinkClicks();
	}
  
	/**
	 * 绑定链接点击事件，判断是否需要新标签页打开
	 */
	bindLinkClicks() {
	  document.addEventListener('click', (e) => {
		const link = e.target.closest('.page-link, .nav-page-link');
		if (!link) return;
  
		const targetToolId = link.dataset.toolId;
		const href = link.getAttribute('href');
  
		// 如果是不同工具集，在新标签页打开
		if (targetToolId && targetToolId !== this.currentToolId) {
		  e.preventDefault();
		  window.open(href, '_blank');
		}
		// 同一工具集内，当前页跳转（默认行为）
	  });
	}
  }
  
  // 智能初始化：支持defer和直接加载两种方式
  function initNav() {
	new HaixinNav();
  }
  
  if (document.readyState === 'loading') {
	// DOM还在加载中，等待DOMContentLoaded事件
	document.addEventListener('DOMContentLoaded', initNav);
  } else {
	// DOM已经加载完成，直接初始化
	initNav();
  }
  
  