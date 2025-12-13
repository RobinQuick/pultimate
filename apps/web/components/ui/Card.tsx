export function Card({ children, className = "" }: { children: React.ReactNode, className?: string }) {
    return (
        <div className={`bg-white rounded-lg border border-slate-200 shadow-sm ${className}`}>
            {children}
        </div>
    );
}

export function CardHeader({ children, className = "" }: { children: React.ReactNode, className?: string }) {
    return <div className={`p-6 border-b border-slate-100 ${className}`}>{children}</div>;
}

export function CardTitle({ children }: { children: React.ReactNode }) {
    return <h3 className="text-lg font-medium text-slate-900">{children}</h3>;
}

export function CardContent({ children, className = "" }: { children: React.ReactNode, className?: string }) {
    return <div className={`p-6 ${className}`}>{children}</div>;
}
