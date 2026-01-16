/**
 * Eleventy Configuration for uu_framework
 * Static site generator for ITAM course materials
 */

const markdownIt = require("markdown-it");
const markdownItContainer = require("markdown-it-container");
const markdownItAttrs = require("markdown-it-attrs");
const markdownItAnchor = require("markdown-it-anchor");
const fs = require("fs");
const path = require("path");

module.exports = function(eleventyConfig) {

  // ============================================
  // Markdown Configuration
  // ============================================

  const mdOptions = {
    html: true,
    breaks: false,
    linkify: true,
    typographer: true
  };

  const md = markdownIt(mdOptions)
    .use(markdownItAttrs)
    .use(markdownItAnchor, {
      permalink: markdownItAnchor.permalink.headerLink(),
      slugify: s => s.toLowerCase().replace(/[^\w]+/g, '-')
    });

  // Custom container for :::homework, :::exercise, etc.
  const componentTypes = ['homework', 'exercise', 'prompt', 'example', 'exam', 'project'];

  componentTypes.forEach(type => {
    md.use(markdownItContainer, type, {
      validate: function(params) {
        return params.trim().match(new RegExp(`^${type}\\s*(.*)$`));
      },
      render: function(tokens, idx) {
        const token = tokens[idx];
        if (token.nesting === 1) {
          // Opening tag - parse attributes
          const match = token.info.trim().match(new RegExp(`^${type}\\s*(.*)$`));
          const attrsStr = match ? match[1] : '';
          const attrs = parseAttributes(attrsStr);
          const attrsHtml = Object.entries(attrs)
            .map(([k, v]) => `data-${k}="${v}"`)
            .join(' ');
          return `<div class="component component--${type}" ${attrsHtml}>\n`;
        } else {
          // Closing tag
          return '</div>\n';
        }
      }
    });
  });

  eleventyConfig.setLibrary("md", md);

  // ============================================
  // Passthrough Copy
  // ============================================

  // Copy CSS (paths relative to input directory)
  eleventyConfig.addPassthroughCopy({ "../uu_framework/eleventy/src/css": "css" });

  // Copy fonts
  eleventyConfig.addPassthroughCopy({ "../uu_framework/eleventy/src/fonts": "fonts" });

  // Copy images from all content subdirectories
  // Convention: images for each section are stored in */images/ subdirectories
  // Match numbered chapters (01_, 02_, etc.) and appendices (a_, b_, etc.)
  ['01', '02', '03', '04', '05', '06', '07', '08', '09', '10'].forEach(num => {
    eleventyConfig.addPassthroughCopy(`${num}_*/**/images/**`);
  });
  ['a', 'b', 'c'].forEach(letter => {
    eleventyConfig.addPassthroughCopy(`${letter}_*/**/images/**`);
  });
  // Also copy root images directory if it exists
  eleventyConfig.addPassthroughCopy({ "images": "images" });

  // Copy PDF files from content directories (exclude b_libros which is gitignored)
  // Match all PDFs in numbered directories (01_, 02_, 03_, etc.)
  ['01', '02', '03', '04', '05', '06', '07', '08', '09'].forEach(num => {
    eleventyConfig.addPassthroughCopy(`${num}_*/**/*.pdf`);
  });
  // Match all PDFs in appendix directories
  eleventyConfig.addPassthroughCopy("a_stack/**/*.pdf");

  // Copy favicon files to site root
  eleventyConfig.addPassthroughCopy("*.ico");
  eleventyConfig.addPassthroughCopy("apple-touch-icon.png");
  eleventyConfig.addPassthroughCopy("favicon*.png");

  // Copy .nojekyll to prevent GitHub Pages from using Jekyll
  eleventyConfig.addPassthroughCopy(".nojekyll");

  // Ignore output directory to prevent scanning it
  eleventyConfig.ignores.add("../_site/**");

  // ============================================
  // Filters
  // ============================================

  // Render markdown content
  eleventyConfig.addFilter("renderMarkdown", function(content) {
    if (!content) return '';
    return md.render(content);
  });

  // Format date in Spanish (Mexico City timezone)
  eleventyConfig.addFilter("formatDate", function(date) {
    if (!date) return '';
    const d = new Date(date + 'T12:00:00');  // Noon to avoid timezone shifts
    return d.toLocaleDateString('es-MX', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
      timeZone: 'America/Mexico_City'
    });
  });

  // Extract title from filename if no frontmatter
  eleventyConfig.addFilter("titleFromFilename", function(filename) {
    if (!filename) return 'Sin titulo';
    // Remove extension and path
    const name = filename.split('/').pop().replace(/\.\w+$/, '');
    // Remove numeric prefix (00_, 01_, etc.)
    const withoutPrefix = name.replace(/^\d+[_-]?/, '');
    // Convert underscores/hyphens to spaces and capitalize
    return withoutPrefix
      .replace(/[_-]/g, ' ')
      .replace(/\b\w/g, l => l.toUpperCase());
  });

  // Get reading order from filename prefix
  eleventyConfig.addFilter("getOrder", function(filename) {
    if (!filename) return 999;
    const match = filename.match(/^(\d+)/);
    return match ? parseInt(match[1], 10) : 999;
  });

  // Get navigation number - uses actual file prefix numbers
  // Examples: a_stack -> A, 02_llms -> A.2, 01_intro -> 1, z_documentacion -> Z
  eleventyConfig.addFilter("getNavNumber", function(name, prefix, index) {
    // Check if name starts with z_ prefix (documentation section)
    if (name.match(/^z_/i)) {
      return 'Z';
    }

    // Check if name starts with letter prefix (a_, b_, c_, etc.) for appendices
    const letterMatch = name.match(/^([a-z])_/i);
    if (letterMatch) {
      return letterMatch[1].toUpperCase();
    }

    // Check if name starts with numeric prefix (01_, 02_, etc.)
    const numMatch = name.match(/^(\d+)[_-]/);
    if (numMatch) {
      const num = parseInt(numMatch[1], 10);
      return prefix + num;
    }

    // Fallback to sequential index if no prefix found
    return prefix + (index + 1);
  });

  // Clean navigation title - remove "Módulo X:", "Module X:", etc.
  eleventyConfig.addFilter("cleanNavTitle", function(title) {
    if (!title) return '';
    let cleaned = title
      .replace(/^\?\?\s*/, '')  // Remove ?? prefix
      .replace(/^Módulo\s*\d+\s*[:\-]\s*/i, '')  // Remove "Módulo X:"
      .replace(/^Module\s*\d+\s*[:\-]\s*/i, '')  // Remove "Module X:"
      .replace(/^Capítulo\s*\d+\s*[:\-]\s*/i, '')  // Remove "Capítulo X:"
      .replace(/^Chapter\s*\d+\s*[:\-]\s*/i, '')  // Remove "Chapter X:"
      .trim();
    return cleaned || title;
  });

  // ============================================
  // Collections
  // ============================================

  // All content pages
  eleventyConfig.addCollection("content", function(collectionApi) {
    return collectionApi.getFilteredByGlob("clase/**/*.md")
      .filter(item => {
        // Exclude non-content files
        if (item.inputPath.includes('b_libros')) return false;
        if (item.inputPath.includes('README_FLOW')) return false;
        if (item.inputPath.includes('task-pages')) return false;
        // Exclude top-bar-only utility pages
        if (item.inputPath.includes('aleatorio.md')) return false;
        // Exclude work-in-progress (??_) directories
        if (item.inputPath.includes('??_')) return false;
        return true;
      })
      .sort((a, b) => {
        const orderA = a.data.order || getOrderFromPath(a.inputPath);
        const orderB = b.data.order || getOrderFromPath(b.inputPath);
        return orderA - orderB;
      });
  });

  // ============================================
  // Documentation (from uu_framework/docs/)
  // Uses docsContent.js data file + clase/docs.njk pagination
  // Rendered to /docs/ path, keeping clase/ clean
  // ============================================

  // Add docs directory to watch targets for hot reload
  eleventyConfig.addWatchTarget("../uu_framework/docs/");

  // ============================================
  // Shortcodes
  // ============================================

  // Icon shortcode (using simple text icons, no dependencies)
  eleventyConfig.addShortcode("icon", function(name) {
    const icons = {
      homework: '[T]',
      exercise: '[E]',
      prompt: '[>]',
      example: '[*]',
      exam: '[!]',
      project: '[P]',
      copy: '[C]',
      check: '[v]',
      arrow: '>'
    };
    return icons[name] || `[${name}]`;
  });

  // ============================================
  // Global Data - Default Layout
  // ============================================

  // Set default layout for all markdown files
  eleventyConfig.addGlobalData("layout", "layouts/base.njk");

  // ============================================
  // Transform - Fix .md links in output HTML
  // ============================================

  eleventyConfig.addTransform("fixMdLinks", function(content, outputPath) {
    if (outputPath && outputPath.endsWith(".html")) {
      // Transform href="...*.md" to href=".../" (remove .md, add trailing slash)
      // Also fix relative paths: ./file.md -> ../file/
      content = content.replace(
        /href="([^"]*?)\.md"/g,
        (match, path) => {
          // Don't transform external URLs
          if (path.startsWith('http://') || path.startsWith('https://')) {
            return match;
          }
          // Transform ./path to ../path (because we're in a subdirectory)
          let newPath = path;
          if (newPath.startsWith('./')) {
            newPath = '../' + newPath.slice(2);
          }
          // Remove .md (already done by regex) and ensure trailing slash
          return `href="${newPath}/"`;
        }
      );

      // Also fix relative image paths: ./images/ -> ../images/
      // Because each page becomes a directory (file.md -> file/index.html)
      content = content.replace(
        /src="\.\/images\//g,
        'src="../images/'
      );

      return content;
    }
    return content;
  });

  // ============================================
  // BrowserSync Configuration (for Docker)
  // ============================================

  eleventyConfig.setBrowserSyncConfig({
    host: "0.0.0.0",
    open: false,
    ui: false
  });

  // ============================================
  // Configuration
  // ============================================

  // Path prefix priority: 1) ENV var, 2) repo.json (from preprocessing), 3) ERROR
  let pathPrefix = process.env.PATH_PREFIX;

  if (!pathPrefix) {
    try {
      // Try to read from generated repo.json
      const fs = require('fs');
      const repoDataPath = path.join(__dirname, '_data', 'repo.json');
      const repoData = JSON.parse(fs.readFileSync(repoDataPath, 'utf-8'));

      if (!repoData.base_url) {
        throw new Error('repo.json exists but base_url is empty');
      }
      pathPrefix = repoData.base_url;
    } catch (err) {
      console.error('\n' + '=' * 60);
      console.error('ERROR: Cannot determine path prefix.');
      console.error('Run preprocessing first: python3 uu_framework/scripts/preprocess.py');
      console.error('=' * 60 + '\n');
      process.exit(1);
    }
  }

  // Ensure trailing slash
  if (!pathPrefix.endsWith('/')) {
    pathPrefix += '/';
  }

  return {
    dir: {
      input: "clase",
      includes: "../uu_framework/eleventy/_includes",
      data: "../uu_framework/eleventy/_data",
      output: "_site"
    },
    templateFormats: ["md", "njk", "html"],
    markdownTemplateEngine: "njk",
    htmlTemplateEngine: "njk",
    pathPrefix: pathPrefix
  };
};

// ============================================
// Helper Functions
// ============================================

/**
 * Parse attributes from string like {id="foo" title="bar"}
 */
function parseAttributes(str) {
  const attrs = {};
  if (!str) return attrs;

  // Match key="value" or key='value' patterns
  const regex = /(\w+)=["']([^"']+)["']/g;
  let match;
  while ((match = regex.exec(str)) !== null) {
    attrs[match[1]] = match[2];
  }
  return attrs;
}

/**
 * Get sort order from file path based on numeric/letter prefix
 * Handles: 00_index, 01_intro, a_stack, b_libros, z_documentacion, etc.
 * Letter prefixes (appendices) sort after all numeric content
 * z_ prefix sorts at the very end (documentation section)
 */
function getOrderFromPath(path) {
  const parts = path.split('/').filter(p => p && p !== '.' && p !== 'clase');
  let order = 0;

  parts.forEach((part, i) => {
    const weight = Math.pow(100, parts.length - i);

    // Check for z_ prefix (documentation) - always last
    if (part.match(/^z_/i)) {
      order += 90 * weight;
      return;
    }

    // Check for letter prefix (a_, b_, c_) - appendices come after numbered content
    const letterMatch = part.match(/^([a-z])_/i);
    if (letterMatch) {
      // Letters start at 50 (after numbers 00-49) plus letter position
      const letterValue = 50 + (letterMatch[1].toLowerCase().charCodeAt(0) - 97);
      order += letterValue * weight;
      return;
    }

    // Check for numeric prefix (00_, 01_, 02_)
    const numMatch = part.match(/^(\d+)/);
    if (numMatch) {
      order += parseInt(numMatch[1], 10) * weight;
      return;
    }

    // No prefix - put at end (99)
    order += 99 * weight;
  });

  return order;
}
