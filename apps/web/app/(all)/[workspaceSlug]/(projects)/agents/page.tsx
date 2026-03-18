/**
 * Copyright (c) 2023-present Plane Software, Inc. and contributors
 * SPDX-License-Identifier: AGPL-3.0-only
 * See the LICENSE file for details.
 */

import { observer } from "mobx-react";
// components
import { PageHead } from "@/components/core/page-title";
// hooks
import { useWorkspace } from "@/hooks/store/use-workspace";

function AgentDashboardPage() {
  const { currentWorkspace } = useWorkspace();
  const pageTitle = currentWorkspace?.name ? `${currentWorkspace?.name} - Agent Dashboard` : "Agent Dashboard";

  return (
    <>
      <PageHead title={pageTitle} />
      <div className="p-6">
        <h1 className="text-2xl font-semibold mb-6">Agent Dashboard</h1>
        
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {/* Active Agents Card */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-medium mb-4">Active Agents</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between p-3 bg-gray-50 rounded">
                <span className="font-medium">nimbus-prime</span>
                <span className="text-green-600 text-sm">● Active</span>
              </div>
            </div>
          </div>

          {/* Claimable Tasks Card */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-medium mb-4">Claimable Tasks</h2>
            <div className="text-3xl font-bold text-blue-600">5</div>
            <p className="text-gray-500 text-sm mt-1">Tasks waiting for agents</p>
          </div>

          {/* Review Queue Card */}
          <div className="bg-white rounded-lg shadow p-6 border border-gray-200">
            <h2 className="text-lg font-medium mb-4">Review Queue</h2>
            <div className="text-3xl font-bold text-orange-600">2</div>
            <p className="text-gray-500 text-sm mt-1">Tasks awaiting review</p>
          </div>
        </div>

        {/* Agent Activity Table */}
        <div className="mt-8 bg-white rounded-lg shadow border border-gray-200">
          <div className="p-6 border-b border-gray-200">
            <h2 className="text-lg font-medium">Agent Activity</h2>
          </div>
          <div className="p-6">
            <div className="overflow-x-auto">
              <table className="w-full text-left">
                <thead>
                  <tr className="border-b border-gray-200">
                    <th className="pb-3 font-medium text-gray-700">Task</th>
                    <th className="pb-3 font-medium text-gray-700">Agent</th>
                    <th className="pb-3 font-medium text-gray-700">Status</th>
                    <th className="pb-3 font-medium text-gray-700">Started</th>
                  </tr>
                </thead>
                <tbody>
                  <tr>
                    <td className="py-3">Research Django Channels</td>
                    <td className="py-3">nimbus-prime</td>
                    <td className="py-3">
                      <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm">In Progress</span>
                    </td>
                    <td className="py-3 text-gray-500">2 min ago</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}

export default observer(AgentDashboardPage);
