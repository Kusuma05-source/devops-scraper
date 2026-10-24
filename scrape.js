const puppeteer = require("puppeteer");
const fs = require("fs");

// URL comes from CLI arg or SCRAPE_URL env var
const url = process.argv[2] || process.env.SCRAPE_URL;
const outFile = process.env.OUTPUT_FILE || "scraped_data.json";

if (!url) {
  console.error("Error: provide a URL via SCRAPE_URL env var or as first argument.");
  process.exit(1);
}

try {
  new URL(url);
} catch {
  console.error(`Error: invalid URL -> ${url}`);
  process.exit(1);
}

(async () => {
  let browser;
  try {
    browser = await puppeteer.launch({
      headless: "new",
      executablePath: process.env.PUPPETEER_EXECUTABLE_PATH || "/usr/bin/chromium",
      args: [
        "--no-sandbox",
        "--disable-setuid-sandbox",
        "--disable-dev-shm-usage",
        "--disable-gpu",
      ],
    });

    const page = await browser.newPage();
    console.log(`Scraping: ${url}`);
    await page.goto(url, { waitUntil: "networkidle2", timeout: 60000 });

    const data = await page.evaluate(() => ({
      title: document.title || null,
      first_heading: document.querySelector("h1")?.innerText.trim() || null,
      meta_description:
        document.querySelector('meta[name="description"]')?.content || null,
      link_count: document.querySelectorAll("a").length,
    }));

    data.url = url;
    data.scraped_at = new Date().toISOString();

    fs.writeFileSync(outFile, JSON.stringify(data, null, 2));
    console.log(`Saved to ${outFile}:`, data);
  } catch (err) {
    console.error("Scrape failed:", err.message);
    process.exitCode = 1;
  } finally {
    if (browser) await browser.close();
  }
})();
