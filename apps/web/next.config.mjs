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
    }
};

export default nextConfig;
