// src/components/ui/DataTable.jsx
import React, { useState } from 'react';
import { ChevronDown, ChevronUp, ChevronsUpDown, Search, Filter } from 'lucide-react';
import { SearchInput } from './Input';
import { IconButton } from './Button';

const DataTable = ({
  columns,
  data,
  pageSize = 10,
  searchable = false,
  filterable = false,
  sortable = true,
  selectable = false,
  onRowClick,
  className = '',
  ...props
}) => {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortColumn, setSortColumn] = useState('');
  const [sortDirection, setSortDirection] = useState('asc');
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedRows, setSelectedRows] = useState([]);
  const [filters, setFilters] = useState({});

  const totalPages = Math.ceil(data.length / pageSize);
  const startIndex = (currentPage - 1) * pageSize;
  const endIndex = startIndex + pageSize;

  const handleSort = (columnId) => {
    if (!sortable) return;
    
    if (sortColumn === columnId) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortColumn(columnId);
      setSortDirection('asc');
    }
  };

  const getSortIcon = (columnId) => {
    if (sortColumn !== columnId) {
      return <ChevronsUpDown className="w-4 h-4" />;
    }
    return sortDirection === 'asc' ? (
      <ChevronUp className="w-4 h-4" />
    ) : (
      <ChevronDown className="w-4 h-4" />
    );
  };

  const filteredData = data.filter(row => {
    if (searchTerm) {
      const searchableText = Object.values(row).join(' ').toLowerCase();
      return searchableText.includes(searchTerm.toLowerCase());
    }
    return true;
  });

  const sortedData = [...filteredData].sort((a, b) => {
    if (!sortColumn) return 0;
    
    const aValue = a[sortColumn];
    const bValue = b[sortColumn];
    
    if (aValue < bValue) return sortDirection === 'asc' ? -1 : 1;
    if (aValue > bValue) return sortDirection === 'asc' ? 1 : -1;
    return 0;
  });

  const paginatedData = sortedData.slice(startIndex, endIndex);

  return (
    <div className={`space-y-4 ${className}`} {...props}>
      {/* Table Controls */}
      <div className="flex items-center justify-between">
        {searchable && (
          <div className="flex-1 max-w-md">
            <SearchInput
              placeholder="Search..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
        )}
        
        <div className="flex items-center gap-2">
          {filterable && (
            <IconButton icon={Filter} variant="secondary" />
          )}
        </div>
      </div>

      {/* Table */}
      <div className="border border-white/10 rounded overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="bg-white/5 border-b border-white/10">
              {selectable && (
                <th className="py-3 px-4 text-left">
                  <input
                    type="checkbox"
                    className="rounded border-white/20 bg-white/5"
                  />
                </th>
              )}
              
              {columns.map(column => (
                <th
                  key={column.id}
                  className="py-3 px-4 text-left text-sm font-medium text-white/60"
                >
                  <button
                    onClick={() => handleSort(column.id)}
                    className="flex items-center gap-2 hover:text-white transition-colors"
                    disabled={!sortable}
                  >
                    {column.header}
                    {sortable && getSortIcon(column.id)}
                  </button>
                </th>
              ))}
            </tr>
          </thead>
          
          <tbody>
            {paginatedData.map((row, index) => (
              <tr
                key={index}
                className={`
                  border-b border-white/5 last:border-0
                  ${onRowClick ? 'cursor-pointer hover:bg-white/5' : ''}
                `}
                onClick={() => onRowClick && onRowClick(row)}
              >
                {selectable && (
                  <td className="py-3 px-4">
                    <input
                      type="checkbox"
                      className="rounded border-white/20 bg-white/5"
                      checked={selectedRows.includes(row.id)}
                      onChange={(e) => {
                        if (e.target.checked) {
                          setSelectedRows([...selectedRows, row.id]);
                        } else {
                          setSelectedRows(selectedRows.filter(id => id !== row.id));
                        }
                      }}
                    />
                  </td>
                )}
                
                {columns.map(column => (
                  <td key={column.id} className="py-3 px-4">
                    {column.render ? column.render(row[column.id], row) : row[column.id]}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination */}
      <div className="flex items-center justify-between">
        <div className="text-sm text-white/60">
          Showing {startIndex + 1}-{Math.min(endIndex, filteredData.length)} of {filteredData.length} results
        </div>
        
        <div className="flex items-center gap-2">
          <button
            onClick={() => setCurrentPage(prev => Math.max(1, prev - 1))}
            disabled={currentPage === 1}
            className="px-3 py-1.5 border border-white/20 rounded text-sm disabled:opacity-50"
          >
            Previous
          </button>
          
          <div className="flex items-center gap-1">
            {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
              let pageNum;
              if (totalPages <= 5) {
                pageNum = i + 1;
              } else if (currentPage <= 3) {
                pageNum = i + 1;
              } else if (currentPage >= totalPages - 2) {
                pageNum = totalPages - 4 + i;
              } else {
                pageNum = currentPage - 2 + i;
              }
              
              return (
                <button
                  key={pageNum}
                  onClick={() => setCurrentPage(pageNum)}
                  className={`
                    w-8 h-8 rounded text-sm
                    ${currentPage === pageNum
                      ? 'bg-white text-black'
                      : 'border border-white/20 hover:bg-white/5'
                    }
                  `}
                >
                  {pageNum}
                </button>
              );
            })}
          </div>
          
          <button
            onClick={() => setCurrentPage(prev => Math.min(totalPages, prev + 1))}
            disabled={currentPage === totalPages}
            className="px-3 py-1.5 border border-white/20 rounded text-sm disabled:opacity-50"
          >
            Next
          </button>
        </div>
      </div>
    </div>
  );
};

export default DataTable;