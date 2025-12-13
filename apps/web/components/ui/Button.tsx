export type ButtonProps = React.ButtonHTMLAttributes<HTMLButtonElement> & {
    variant?: 'primary' | 'secondary' | 'outline' | 'danger';
    size?: 'sm' | 'md' | 'lg';
};

export const Button: React.FC<ButtonProps> = ({
    variant = 'primary',
    size = 'md',
    className = '',
    ...props
}) => {
    const baseStyle = "inline-flex items-center justify-center rounded-md font-medium transition-colors focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:pointer-events-none";

    const variants = {
        primary: "bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500 border border-transparent shadow-sm",
        secondary: "bg-slate-100 text-slate-900 hover:bg-slate-200 focus:ring-slate-500 border border-transparent",
        outline: "bg-transparent border border-slate-300 text-slate-700 hover:bg-slate-50 focus:ring-slate-500",
        danger: "bg-red-600 text-white hover:bg-red-700 focus:ring-red-500 border border-transparent"
    };

    const sizes = {
        sm: "h-8 px-3 text-xs",
        md: "h-10 px-4 py-2 text-sm",
        lg: "h-12 px-6 text-base"
    };

    return (
        <button
            className={`${baseStyle} ${variants[variant]} ${sizes[size]} ${className}`}
            {...props}
        />
    );
};
