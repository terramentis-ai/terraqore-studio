
import React, { useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { AgentNode, AgentStatus, AgentType } from '../types';
import { COLORS } from '../constants';

interface AgentFlowProps {
  data: AgentNode[];
  activeNodeId: string | null;
  onNodeClick: (id: string) => void;
  dynamicIcons: Record<string, string>;
}

const FALLBACK_ICONS: Record<string, string> = {
  [AgentType.META]: "M-5,2 L0,-10 L5,2 L-1,2 L1,10 Z",
  [AgentType.ORCHESTRATOR]: "M-8,-2 L0,2 L8,-2 L0,-6 Z M-8,4 L0,8 L8,4 L0,0 Z M-8,-8 L0,-4 L8,-8 L0,-12 Z",
  [AgentType.RESEARCHER]: "M-3,-3 A5,5 0 1 0 5,5 M3,3 L8,8",
  [AgentType.CODER]: "M-6,-5 L-10,0 L-6,5 M6,-5 L10,0 L6,5 M-2,7 L2,-7",
  [AgentType.ANALYST]: "M-6,6 L-6,-2 M0,6 L0,-8 M6,6 L6,2",
  [AgentType.REVIEWER]: "M0,-9 L-8,-5 L-8,2 C-8,7 0,10 0,10 C0,10 8,7 8,2 L8,-5 Z",
  [AgentType.EXECUTOR]: "M-6,-6 H6 V6 H-6 Z M0,-6 V-9 M0,6 V9 M-6,0 H-9 M6,0 H9",
};

const AgentFlow: React.FC<AgentFlowProps> = ({ data, activeNodeId, onNodeClick, dynamicIcons }) => {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || !data.length) return;

    const svg = d3.select(svgRef.current);
    svg.selectAll('*').remove();

    const width = svgRef.current.clientWidth;
    const height = svgRef.current.clientHeight;

    const container = svg.append('g').attr('class', 'viz-container');

    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        container.attr('transform', event.transform);
      });

    svg.call(zoom);

    const root = d3.hierarchy(data[0]);
    const treeLayout = d3.tree<AgentNode>().size([width - 240, height - 240]);
    treeLayout(root);

    const initialTransform = d3.zoomIdentity.translate(120, 120);
    svg.call(zoom.transform, initialTransform);

    const defs = svg.append('defs');
    
    // Node Glows
    Object.entries(COLORS).forEach(([key, color]) => {
      const grad = defs.append('radialGradient')
        .attr('id', `grad-${key.toLowerCase()}`)
        .attr('cx', '50%')
        .attr('cy', '50%')
        .attr('r', '50%');
      grad.append('stop').attr('offset', '0%').attr('stop-color', color).attr('stop-opacity', 0.25);
      grad.append('stop').attr('offset', '100%').attr('stop-color', color).attr('stop-opacity', 0);
    });

    const linkGroup = container.append('g').attr('class', 'links');
    const updateLinks = () => {
      linkGroup.selectAll('.link')
        .data(root.links())
        .join('path')
        .attr('class', 'link')
        .attr('d', d3.linkVertical()
          .x(d => (d as any).x)
          .y(d => (d as any).y) as any
        )
        .attr('fill', 'none')
        .attr('stroke', 'rgba(255,255,255,0.05)')
        .attr('stroke-width', 1.5);
    };
    updateLinks();

    const nodeGroup = container.selectAll('.node')
      .data(root.descendants())
      .enter()
      .append('g')
      .attr('class', d => `node status-${d.data.status}`)
      .attr('transform', d => `translate(${(d as any).x}, ${(d as any).y})`)
      .style('cursor', 'grab')
      .on('click', (event, d) => {
        event.stopPropagation();
        onNodeClick(d.data.id);
      })
      .call(d3.drag<SVGGElement, d3.HierarchyPointNode<AgentNode>>()
        .on('start', function() { d3.select(this).style('cursor', 'grabbing').raise(); })
        .on('drag', function(event, d) {
          (d as any).x = event.x;
          (d as any).y = event.y;
          d3.select(this).attr('transform', `translate(${event.x}, ${event.y})`);
          updateLinks();
        })
        .on('end', function() { d3.select(this).style('cursor', 'grab'); })
      );

    nodeGroup.each(function(d) {
      const el = d3.select(this);
      const isActive = d.data.id === activeNodeId;
      const isBusy = d.data.status === AgentStatus.THINKING || d.data.status === AgentStatus.EXECUTING;
      const baseColor = (COLORS as any)[d.data.type.split(' ')[0].toUpperCase()] || '#52525b';

      // Background Aura
      el.append('circle')
        .attr('r', 50)
        .attr('fill', `url(#grad-${d.data.type.split(' ')[0].toLowerCase()})`)
        .attr('opacity', isBusy || isActive ? 1 : 0.3);

      // Node Body (3D Material Look)
      if (d.data.type === AgentType.META) {
        el.append('path')
          .attr('d', 'M 0 -30 L 30 0 L 0 30 L -30 0 Z')
          .attr('fill', '#080808')
          .attr('stroke', isActive ? '#fff' : 'rgba(255,255,255,0.1)')
          .attr('stroke-width', isActive ? 3 : 1.5)
          .attr('class', isBusy ? 'animate-glow' : '');
      } else {
        el.append('rect')
          .attr('x', -40).attr('y', -22).attr('width', 80).attr('height', 44).attr('rx', 12)
          .attr('fill', '#080808')
          .attr('stroke', isActive ? '#fff' : 'rgba(255,255,255,0.1)')
          .attr('stroke-width', isActive ? 3 : 1.5)
          .attr('class', isBusy ? 'animate-glow' : '');
      }

      // Icon
      const iconPath = dynamicIcons[d.data.type] || FALLBACK_ICONS[d.data.type];
      if (iconPath) {
        el.append('path')
          .attr('d', iconPath)
          .attr('fill', 'none')
          .attr('stroke', isActive ? '#fff' : baseColor)
          .attr('stroke-width', 2)
          .attr('stroke-linecap', 'round')
          .attr('transform', 'scale(1.2)');
      }

      // Label & Status
      el.append('text')
        .attr('dy', 55).attr('text-anchor', 'middle')
        .attr('fill', '#fff').attr('font-size', '10px').attr('font-weight', '700').attr('letter-spacing', '0.02em')
        .text(d.data.label);

      el.append('text')
        .attr('dy', 68).attr('text-anchor', 'middle')
        .attr('fill', d.data.status === AgentStatus.COMPLETED ? '#10b981' : d.data.status === AgentStatus.FAILED ? '#ef4444' : '#71717a')
        .attr('font-size', '8px').attr('font-weight', '900').attr('letter-spacing', '0.1em')
        .text(d.data.status.toUpperCase());
    });

  }, [data, activeNodeId, onNodeClick, dynamicIcons]);

  return (
    <div className="w-full h-full bg-[#030303] relative overflow-hidden">
      <div className="absolute inset-0 bg-[radial-gradient(#ffffff08_1px,transparent_1px)] [background-size:40px_40px] opacity-40"></div>
      
      <div className="absolute top-10 left-10 z-20 flex flex-col gap-6">
        <div className="space-y-2">
          <div className="flex items-center gap-3">
             <div className="w-3 h-3 rounded-full bg-purple-500 shadow-[0_0_15px_#a855f7]"></div>
             <h3 className="text-[12px] font-black text-white uppercase tracking-[0.4em]">Topology Cluster Alpha</h3>
          </div>
          <p className="text-[9px] text-zinc-500 uppercase tracking-widest font-bold pl-6">Workspace v3.0 (Drag & Fluid Interaction)</p>
        </div>
      </div>

      <svg ref={svgRef} className="w-full h-full relative z-10" />
      
      <style>{`
        .animate-glow { animation: nodeGlow 2s ease-in-out infinite; }
        @keyframes nodeGlow { 0%, 100% { filter: brightness(1) drop-shadow(0 0 5px rgba(168, 85, 247, 0.2)); } 50% { filter: brightness(1.5) drop-shadow(0 0 20px rgba(168, 85, 247, 0.5)); } }
        .viz-container { transition: transform 0.2s cubic-bezier(0, 0, 0.2, 1); }
      `}</style>
    </div>
  );
};

export default AgentFlow;
