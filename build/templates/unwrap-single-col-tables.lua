-- unwrap-single-col-tables.lua
-- Pandoc Lua filter: replace single-column tables with their cell contents.
-- Multi-column tables are left as-is.
function Table(tbl)
  if #tbl.colspecs ~= 1 then return nil end  -- keep multi-column tables

  local blocks = {}

  -- body rows only (skip the header row which is just the column label)
  for _, body in ipairs(tbl.bodies) do
    for _, row in ipairs(body.body) do
      for _, cell in ipairs(row.cells) do
        for _, block in ipairs(cell.contents) do
          table.insert(blocks, block)
        end
      end
    end
  end

  return blocks
end
