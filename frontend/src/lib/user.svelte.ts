export const userState = $state({
    profile: null as { email: string, full_name: string | null, role: string } | null,
});

export const alertState = $state({
    unreadCount: 0,

    async refresh() {
        const token = localStorage.getItem('access_token');
        if (!token) return;
        try {
            const res = await fetch('http://127.0.0.1:8000/api/v1/alerts/?include_resolved=false', {
                headers: { Authorization: `Bearer ${token}` }
            });
            if (res.ok) {
                const data = await res.json();
                this.unreadCount = data.filter((a: any) => !a.is_read).length;
            }
        } catch { /* silent */ }
    }
});
