// 在Chrome控制台运行此代码获取Cookie
(async () => {
    const cookies = await cookieStore.getCookies();
    const tycCookies = cookies.filter(c => c.domain.includes('tianyancha'));
    console.log(JSON.stringify(tycCookies, null, 2));
    
    // 复制到剪贴板
    if (tycCookies.length > 0) {
        await navigator.clipboard.writeText(JSON.stringify(tycCookies, null, 2));
        console.log('\n已复制到剪贴板！');
    } else {
        console.log('\n未找到天眼查Cookie，请先访问 tianyancha.com 并登录');
    }
})();
