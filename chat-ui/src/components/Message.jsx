function splitTableRow(row) {
  return row
    .trim()
    .replace(/^\|/, "")
    .replace(/\|$/, "")
    .split("|")
    .map((cell) => cell.trim());
}

function markdownTable(text) {
  const lines = text.split("\n").map((line) => line.trim()).filter(Boolean);
  const separatorIndex = lines.findIndex((line) =>
    /^\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)+\|?$/.test(line)
  );

  if (separatorIndex < 1) return null;

  const headers = splitTableRow(lines[separatorIndex - 1]);
  const rows = lines.slice(separatorIndex + 1)
    .filter((line) => line.includes("|"))
    .map(splitTableRow);

  if (!headers.length || !rows.length) return null;
  return { headers, rows };
}

function ProductTable({ headers, rows }) {
  return (
    <div className="product-table-wrap">
      <table className="product-table">
        <thead>
          <tr>
            {headers.map((header) => <th key={header}>{header}</th>)}
          </tr>
        </thead>
        <tbody>
          {rows.map((row, rowIndex) => (
            <tr key={rowIndex}>
              {headers.map((_, cellIndex) => (
                <td key={cellIndex}>{row[cellIndex] || "-"}</td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function Message({ sender, text, time }) {
  const isUser = sender === "user";
  let records = null;
  const markdown = !isUser ? markdownTable(text) : null;

  if (!isUser) {
    try {
      const parsed = JSON.parse(text);
      const rows = Array.isArray(parsed) ? parsed : [parsed];
      if (
        rows.length &&
        rows.every((item) => item && typeof item === "object") &&
        rows.some((item) =>
          ("price" in item && "stock" in item) ||
          ("name" in item && "email" in item)
        )
      ) {
        records = rows;
      }
    } catch {
      records = null;
    }
  }

  return (
    <div className={`message-row ${isUser ? "user-row" : "assistant-row"}`}>

      {!isUser && (
        <div className="message-avatar assistant-avatar">
          🤖
        </div>
      )}

      <div className={`message-content ${isUser ? "user-content" : ""}`}>

        <div
          className={`message-bubble ${
            isUser ? "user-message" : "assistant-message"
          }`}
        >
          {markdown ? (
            <ProductTable {...markdown} />
          ) : records ? (
            records.length ? (
              <div className="product-table-wrap">
                <table className="product-table">
                  <thead>
                    <tr>
                      {"email" in records[0] ? (
                        <>
                          <th>Name</th>
                          <th>Email</th>
                          <th>Created</th>
                        </>
                      ) : (
                        <>
                          <th>Product</th>
                          <th>Description</th>
                          <th>Price</th>
                          <th>Stock</th>
                        </>
                      )}
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((record) => (
                      <tr key={record.id ?? record.email ?? record.name}>
                        {"email" in record ? (
                          <>
                            <td>{record.name}</td>
                            <td>{record.email}</td>
                            <td>{record.created_at || "-"}</td>
                          </>
                        ) : (
                          <>
                            <td>{record.name}</td>
                            <td>{record.description || "-"}</td>
                            <td>{Number(record.price).toFixed(2)}</td>
                            <td>{record.stock}</td>
                          </>
                        )}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            ) : (
              "No records found."
            )
          ) : (
            text
          )}
        </div>

        <span className="message-time">
          {time}
        </span>

      </div>

      {isUser && (
        <div className="message-avatar user-avatar">
          SR
        </div>
      )}

    </div>
  );
}

export default Message;
