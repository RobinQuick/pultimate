/** @type {import('next').NextConfig} */
const nextConfig = {
    output: "standalone",
    // Allow images if needed later
    images: {
        remotePatterns: [
            {
                protocol: "http",
                hostname: "localhost",
            }
        ]
    },
    async redirects() {
        return [
            { source: '/dashboard', destination: '/app/dashboard', permanent: false },
            { source: '/decks', destination: '/app/decks', permanent: false },
            { source: '/templates', destination: '/app/templates', permanent: false },
            { source: '/jobs', destination: '/app/jobs', permanent: false },
            { source: '/rebuild', destination: '/app/rebuild', permanent: false },
        ]
    }
};

export default nextConfig;
