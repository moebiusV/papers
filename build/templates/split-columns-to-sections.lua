-- split-columns-to-sections.lua
-- Pandoc Lua filter: convert multi-column tables to sequential sections.
-- Single-column tables are passed through unchanged.
-- Each column becomes: ### Header, then its paragraphs in order.
-- Used for literary comparison texts (Kafka, Kleist, Marx) where the
-- side-by-side HTML layout doesn't translate to readable markdown.

function Table(tbl)
  if #tbl.colspecs <= 1 then return nil end  -- leave single-column tables alone

  local blocks = {}

  -- collect column headers from the head
  local headers = {}
  for _, row in ipairs(tbl.head.rows) do
    for j, cell in ipairs(row.cells) do
      local text = pandoc.utils.stringify(cell.contents)
      if text ~= "" then headers[j] = text end
    end
  end

  -- collect body content column by column
  local columns = {}
  for j = 1, #tbl.colspecs do columns[j] = {} end

  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.body) do
      for j, cell in ipairs(row.cells) do
        for _, block in ipairs(cell.contents) do
          table.insert(columns[j], block)
        end
      end
    end
  end

  -- emit: header then content, per column
  for j = 1, #tbl.colspecs do
    if headers[j] then
      table.insert(blocks, pandoc.Header(3, headers[j]))
    end
    for _, block in ipairs(columns[j]) do
      table.insert(blocks, block)
    end
  end

  return blocks
end
